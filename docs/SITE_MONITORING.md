# Site change monitoring

`scripts/site_snapshot.py` fetches the public URLs in `data/tools.json` and saves normalized page text plus response metadata. The HTTP baseline lives in `data/site-snapshots/`: one readable text file per captured tool and a `manifest.json` with the URL, final URL, HTTP status, title, content hash, and capture state. It contains no cookies or roster data. The manifest is versioned. Full page-text snapshots stay local and are ignored by Git because this repository is public and the text belongs to other sites. Keep a private copy of the folder if you want detailed diffs on another machine; the manifest alone can still detect hash changes.

Create the first baseline:

```sh
python3 scripts/site_snapshot.py baseline
```

Check the current sites against it:

```sh
python3 scripts/site_snapshot.py check
```

The check writes `out/site-check/report.json`. It leaves the baseline untouched. Run a small diagnostic capture with `--id TOOL_ID --output /tmp/site-capture`; a partial capture cannot replace the shared baseline. Other options include `--workers` (1–16, default 8) and `--timeout` (seconds, default 15). To establish a new approved baseline, run `baseline --output PATH`, inspect the files, and replace the existing baseline deliberately with `--replace`.

For important JavaScript-heavy or inconclusive pages, add `--browser`. This uses the optional `agent-browser` CLI (pinned to 0.38.1) through `npx` and saves rendered text in `data/rendered-snapshots/` with a separate manifest. Browser baselines may cover a selected set of `--id` values. A later `check --browser` uses that saved set by default. Browser checks are slower (two workers by default) and can still be blocked by consent walls or login.

## How to use the signals

- `text_changed` or `metadata_changed`: inspect the diff, then use a browser to verify any changed group-generation features, pricing, access, exports, or privacy claims before editing the review dataset.
- `same_text`: the fetched text matched. This does **not** prove an interactive app is unchanged; JavaScript, account flows, and solver behavior may change without affecting initial HTML.
- `http_error`, `fetch_error`, `thin_page`, `non_html`, or `too_large`: inconclusive. Retry or check in a browser. A 403 from an automated request is not evidence that the site is down for users.

The HTTP collector uses the page body while removing script, style, navigation, footer, and aside text. It normalizes whitespace to reduce harmless diffs, but dynamic text may still produce false positives. Each tool snapshot is capped at 120,000 characters and each HTTP download at 2 MB; the manifest marks truncation. The snapshot is a review aid, not an archival copy or a substitute for testing the actual generator.

For the first update pass, there is no historical page baseline to compare against. Use the new snapshots together with the existing review record, release notes, issue reports, and live browser checks to prioritize full reviews. Record the review date and evidence when changing a rating or feature value.

The first sweep's review leads are recorded in [the 2026-09-22 update pass](UPDATE_PASS_2026-09-22.md).
