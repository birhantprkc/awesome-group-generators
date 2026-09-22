#!/usr/bin/env python3
"""Capture comparable public-page text for the ranked tool URLs.

This is a change detector, not a reviewer. A changed snapshot is a review lead;
an unchanged snapshot cannot prove that a JavaScript app still behaves the same.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "tools.json"
BASELINE = ROOT / "data" / "site-snapshots"
BROWSER_BASELINE = ROOT / "data" / "rendered-snapshots"
MAX_BYTES = 2_000_000
MAX_TEXT = 120_000
BLOCK_TAGS = {
    "address", "article", "blockquote", "br", "button", "dd", "div", "dl",
    "dt", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr",
    "li", "main", "ol", "p", "section", "table", "td", "th", "tr", "ul",
}
SKIP_TAGS = {"script", "style", "svg", "canvas", "noscript", "template"}
BOILERPLATE_TAGS = {"nav", "footer", "aside"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class PageText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.parts: dict[str, list[str]] = {"body": [], "main": [], "article": []}
        self.title_parts: list[str] = []
        self.description = ""

    def active_scopes(self) -> list[str]:
        if any(skipped for _, skipped in self.stack):
            return []
        tags = {tag for tag, _ in self.stack}
        return [scope for scope in self.parts if scope in tags]

    def add(self, value: str) -> None:
        for scope in self.active_scopes():
            self.parts[scope].append(value)

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        attrs = dict(attributes)
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content") or ""
        hidden = attrs.get("hidden") is not None or attrs.get("aria-hidden") == "true"
        skipped = tag in SKIP_TAGS or tag in BOILERPLATE_TAGS or hidden
        self.stack.append((tag, skipped))
        if tag in BLOCK_TAGS:
            self.add("\n")
        if tag == "input" and attrs.get("type", "").lower() not in {"hidden", "password"}:
            label = attrs.get("aria-label") or attrs.get("placeholder")
            if label:
                self.add(f" [input: {label}] ")
        if tag in VOID_TAGS:
            self.stack.pop()

    def handle_startendtag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attributes)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK_TAGS:
            self.add("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, value: str) -> None:
        if any(tag == "title" for tag, _ in self.stack):
            self.title_parts.append(value)
        if value.strip():
            self.add(value)


def normalize(parts: list[str]) -> str:
    lines: list[str] = []
    for raw_line in " ".join(parts).split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return "\n".join(lines)


def extract(html: str) -> tuple[str, str, bool]:
    parser = PageText()
    parser.feed(html)
    title = re.sub(r"\s+", " ", " ".join(parser.title_parts)).strip()
    candidates = [(scope, normalize(parser.parts[scope])) for scope in ("body", "main", "article")]
    # Pricing, privacy, and help text often live outside <main>; prefer the
    # complete body after removing navigation/footer/aside boilerplate.
    text = next((value for _, value in candidates if len(value) >= 200), candidates[0][1])
    if parser.description:
        text = f"Description: {re.sub(r'\s+', ' ', parser.description).strip()}\n{text}"
    truncated = len(text) > MAX_TEXT
    return title, text[:MAX_TEXT].rstrip() + "\n", truncated


def capture(tool: dict, timeout: float) -> tuple[dict, str | None]:
    record = {"id": tool["id"], "rank": tool["rank"], "name": tool["name"], "url": tool["url"]}
    request = Request(
        tool["url"],
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AwesomeGroupGenerators/1.0; public review monitor)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            record["status"] = response.status
            record["finalUrl"] = response.geturl()
            record["contentType"] = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            content = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        record.update(status=error.code, finalUrl=error.geturl(), state="http_error")
        return record, None
    except (URLError, TimeoutError, OSError, ValueError) as error:
        record.update(state="fetch_error", error=f"{type(error).__name__}: {error.reason if isinstance(error, URLError) else error}"[:300])
        return record, None
    if len(content) > MAX_BYTES:
        record.update(state="too_large", bytesRead=len(content))
        return record, None
    if record["contentType"] not in {"text/html", "application/xhtml+xml"}:
        record["state"] = "non_html"
        return record, None
    try:
        html = content.decode(charset, errors="replace")
    except LookupError:
        html = content.decode("utf-8", errors="replace")
    title, snapshot, truncated = extract(html)
    record.update(
        state="captured" if len(snapshot) >= 200 else "thin_page",
        title=title,
        chars=len(snapshot),
        truncated=truncated,
        sha256=hashlib.sha256(snapshot.encode("utf-8")).hexdigest(),
    )
    return record, snapshot


def capture_browser(tool: dict, timeout: float) -> tuple[dict, str | None]:
    """Capture rendered text with the optional agent-browser CLI."""
    record = {"id": tool["id"], "rank": tool["rank"], "name": tool["name"], "url": tool["url"], "captureMode": "browser"}
    if shutil.which("npx") is None:
        record.update(state="browser_unavailable", error="npx is required for agent-browser")
        return record, None
    session = f"agg-{tool['id']}-{os.getpid()}"
    prefix = ["npx", "--yes", "agent-browser@0.38.1", "--session", session]

    def command(*arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [*prefix, *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, check=False,
        )

    try:
        opened = command("open", tool["url"])
        if opened.returncode:
            record.update(state="browser_error", error=opened.stderr.decode("utf-8", errors="replace")[:300])
            return record, None
        body = command("get", "text", "body")
        title_result = command("get", "title")
        url_result = command("get", "url")
    except (subprocess.TimeoutExpired, OSError) as error:
        record.update(state="browser_error", error=f"{type(error).__name__}: {error}"[:300])
        return record, None
    finally:
        try:
            command("close")
        except (subprocess.TimeoutExpired, OSError):
            pass
    if body.returncode or not body.stdout:
        record.update(state="browser_error", error=body.stderr.decode("utf-8", errors="replace")[:300])
        return record, None
    rendered = body.stdout.decode("utf-8", errors="replace")
    if len(rendered) > MAX_BYTES:
        record.update(state="too_large", bytesRead=len(rendered))
        return record, None
    snapshot = normalize([rendered])[:MAX_TEXT].rstrip() + "\n"
    title = title_result.stdout.decode("utf-8", errors="replace").strip() if title_result.returncode == 0 else ""
    record.update(
        state="captured" if len(snapshot) >= 200 else "thin_page",
        title=title,
        finalUrl=url_result.stdout.decode("utf-8", errors="replace").strip() if url_result.returncode == 0 else None,
        chars=len(snapshot),
        truncated=len(rendered) > MAX_TEXT,
        sha256=hashlib.sha256(snapshot.encode("utf-8")).hexdigest(),
    )
    return record, snapshot


def selected_tools(ids: set[str] | None) -> list[dict]:
    tools = json.loads(DATA.read_text(encoding="utf-8"))["tools"]
    if ids:
        tools = [tool for tool in tools if tool["id"] in ids]
        missing = ids - {tool["id"] for tool in tools}
        if missing:
            raise SystemExit(f"Unknown tool ids: {', '.join(sorted(missing))}")
    return tools


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("baseline", "check"))
    parser.add_argument("--id", action="append", dest="ids", help="Only capture this tool id (repeatable)")
    parser.add_argument("--workers", type=int, help="Parallel requests (default 8 HTTP, 2 browser)")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output", type=Path, help="Output folder for baseline or check report")
    parser.add_argument("--replace", action="store_true", help="Allow replacing an existing baseline")
    parser.add_argument("--browser", action="store_true", help="Use local Chrome to render JavaScript before capture")
    args = parser.parse_args()
    workers = args.workers or (2 if args.browser else 8)
    if workers < 1 or workers > (4 if args.browser else 16) or args.timeout <= 0:
        parser.error("workers must be 1-4 in browser mode or 1-16 in HTTP mode; timeout must be positive")
    baseline_dir = BROWSER_BASELINE if args.browser else BASELINE
    ids = set(args.ids) if args.ids else None
    if args.mode == "check" and args.browser and ids is None:
        prior = json.loads((baseline_dir / "manifest.json").read_text(encoding="utf-8"))
        ids = {record["id"] for record in prior["tools"]}
    tools = selected_tools(ids)
    output = args.output or (baseline_dir if args.mode == "baseline" else ROOT / "out" / ("rendered-check" if args.browser else "site-check"))
    if args.mode == "baseline" and args.ids and output == baseline_dir and not args.browser:
        parser.error("partial baselines require a separate --output folder")
    if args.mode == "baseline" and (output / "manifest.json").exists() and not args.replace:
        parser.error("baseline already exists; use --output for a new baseline or --replace deliberately")
    output.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    snapshots: dict[str, str] = {}
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        capture_fn = capture_browser if args.browser else capture
        futures = {pool.submit(capture_fn, tool, args.timeout): tool["id"] for tool in tools}
        for future in as_completed(futures):
            tool_id = futures[future]
            try:
                record, snapshot = future.result()
            except Exception as error:
                record, snapshot = {"id": tool_id, "state": "unexpected_error", "error": str(error)[:300]}, None
            records[tool_id] = record
            if snapshot is not None:
                snapshots[tool_id] = snapshot
    ordered = [records[tool["id"]] for tool in tools]
    counts: dict[str, int] = {}
    for record in ordered:
        counts[record["state"]] = counts.get(record["state"], 0) + 1
    if args.mode == "baseline":
        if args.replace:
            for old_file in output.glob("*.txt"):
                if old_file.stem not in snapshots:
                    old_file.unlink()
        for tool_id, snapshot in snapshots.items():
            (output / f"{tool_id}.txt").write_text(snapshot, encoding="utf-8")
        manifest = {
            "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "data/tools.json",
            "method": ("local Chrome rendered DOM" if args.browser else "public HTTP HTML") + "; body visible text without navigation/footer/aside, normalized whitespace; not a functional review",
            "counts": counts,
            "tools": ordered,
        }
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        baseline = json.loads((baseline_dir / "manifest.json").read_text(encoding="utf-8"))
        previous = {record["id"]: record for record in baseline["tools"]}
        for record in ordered:
            old = previous.get(record["id"])
            if old is None:
                record["comparison"] = "new_url"
            elif record["state"] not in {"captured", "thin_page"}:
                record["comparison"] = "inconclusive"
            elif old.get("sha256") == record.get("sha256"):
                record["comparison"] = (
                    "metadata_changed"
                    if any(old.get(key) != record.get(key) for key in ("status", "finalUrl", "title"))
                    else "same_text"
                )
            elif old.get("sha256") is None:
                record["comparison"] = "no_baseline_text"
            else:
                record["comparison"] = "text_changed"
                old_path = baseline_dir / f"{record['id']}.txt"
                record["baselineTextAvailable"] = old_path.exists()
                if old_path.exists():
                    old_text = old_path.read_text(encoding="utf-8")
                    record["diffPreview"] = list(difflib.unified_diff(
                        old_text.splitlines(), snapshots[record["id"]].splitlines(),
                        fromfile="baseline", tofile="current", lineterm="", n=2,
                    ))[:80]
        comparison_counts: dict[str, int] = {}
        for record in ordered:
            category = record["comparison"]
            comparison_counts[category] = comparison_counts.get(category, 0) + 1
        report = {
            "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "baselineAt": baseline["createdAt"],
            "counts": counts,
            "comparisonCounts": comparison_counts,
            "tools": ordered,
        }
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.mode}: {len(tools)} URLs in {time.monotonic() - started:.1f}s; " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    if args.mode == "check":
        print("comparison: " + ", ".join(f"{key}={value}" for key, value in sorted(comparison_counts.items())))
    print(output)


if __name__ == "__main__":
    run()
