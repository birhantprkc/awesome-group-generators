# Update-pass triage — 2026-09-22

This document records the lightweight sweep and the targeted reviews that followed it. The initial sweep covered 501 ranked entries. The catalog now has 503: Visimon and three later market finds were added, while two unavailable generators were retired. Sweep signals alone did not change ratings or feature values; the corrections below came from live workflow reviews.

## Baseline

- [HTTP manifest](../data/site-snapshots/manifest.json): 503 current URLs; 421 substantial text captures, 40 thin pages, 25 HTTP errors, and 17 fetch errors. The retired 1000tools and LessonKind URLs are preserved in the out-of-scope record instead of this active baseline.
- [Rendered manifest](../data/rendered-snapshots/manifest.json): 113 priority URLs; 75 substantial captures, 19 thin pages, and 19 browser errors. GroupMixer's initial rendered capture had a transient module-load failure and was retried successfully; its manifest record and local text now contain the complete page.
- Full text snapshots are saved locally in the two baseline folders and ignored by Git. The manifests preserve URLs, response/capture state, title, and text hashes. See [site monitoring](SITE_MONITORING.md) for repeat checks and interpretation.

GPT-5.6 Luna agents compared all 501 HTTP snapshots with the current entries. Their first-pass classifications were 390 `no_clear_change`, 94 `inconclusive`, 10 `possible_change`, and 7 `needs_review`. These are triage labels only: `no_clear_change` does not establish that an interactive workflow still behaves as reviewed. A focused second pass compared 43 possible feature contradictions with the existing feature flags and retained 18 concrete review signals across 11 tools.

## Original priority re-reviews

| Tool | Trigger at the start of this pass |
|---|---|
| [GroupMixer](https://www.groupmixer.app) | The live FAQ describes advanced-generation allowance, verified-account requirements, and Pro access. The current pricing note says there is no subscription or paywall for the solver. Check exact feature gating, cloud-sync processing, and whether account-friction scoring changes. |
| [Smart Group Maker](https://smartgroupmaker.com/) | The current site advertises fixed placements, keep-together/apart relationships, CSV and image export, file import/export, and table editing; several matching feature flags are `no`. A sample run generated groups. Verify enforcement and export files before rescoring. |
| [1000tools Random Pairs Generator](https://1000tools.xyz/random-pairs-generator/) | The current capture appears to show a parked domain instead of the reviewed generator. Confirm in a normal browser and look for a moved URL. |
| [LessonKind Group Maker](https://lessonkind.com/tools/group-maker/) | The captured URL resolves to general teacher tools without the reviewed group-maker workflow. Confirm the route and current availability. |
| [Wordwall Random Team Generator Resource](https://wordwall.net/resource/37278876/random-team-generator) | The resource appears disabled by its owner. Confirm availability and decide whether the entry belongs in the ranked list. |
| [DateRounds](https://daterounds.com/) and [FastRounds](https://fastrounds.com/) | Current pages distinguish paid unlimited events from a free trial. Recheck the stored six-attendee free limit in a live workflow. |
| [Begoodtool Smart Grouping Tool](https://begoodtool.com/smart-grouping/en) | Observed output may conflict with the recorded balanced-size behavior. Repeat with an odd-size roster and inspect the result. |
| [RemagineAI Random Group Generator](https://remagineai.com/name-generator/random-group-generator) | Current page advertises no-login grouping and exports, while the entry records a sign-up-only/inaccessible experience. Test actual generation before changing it. |

## Original feature-flag checks

At the start of this pass, the page or UI mentioned a capability recorded as `no`. The outcomes of live generation and export tests are recorded below:

| Tool | Candidate capability |
|---|---|
| [RandomSelect Group Maker](https://randomselect.net/en/group-maker/) | Keep-together and keep-apart rules; page says best effort, so hard enforcement must be tested. |
| [ToolV Team Generator](https://toolv.com/en/app/team-generator) and [TheToolApp Team Generator](https://thetoolapp.com/generators/team-generator/) | Image download/export. |
| [CodersTool Random Group Generator](https://www.coderstool.com/random-group-generator) | Keep-together and keep-apart controls. |
| [Stilest Random Team Generator](https://www.stilest.com/tools/random-team-generator), [FateFactory Team Splitter](https://www.fatefactory.org/en/team-splitter), [LetsRandomize Random Team Generator](https://letsrandomize.org/tools/random-team-generator/), and [ClassTools24 Random Group Generator](https://classtools24.com/random-group-generator/) | CSV output. |
| [FateWheel Team Generator](https://fatewheel.com/tools/team-generator) and [SpinOfLuck Team Picker Wheel](https://www.spinofluck.com/team-picker) | CSV and image output. |

## Original new-tool intake

[Issue #5](https://github.com/guwidoe/awesome-group-generators/issues/5) contains Chooseday and Visimon. Chooseday exposes a public group generator. A live sample on Visimon produced multiple rounds and an encounter matrix, so it should be evaluated as a repeat-aware breakout planner rather than only a basic randomizer. Initial market candidates for screening are [TeamCreator](https://unitedwetransform.com/team-creator/), [TeamShuffler](https://teamshuffler.com/team-generator), and [Random Wheel Tools' multi-round generator](https://randomwheeltools.com/en/multi-round-group-generator).

The first issue #5 intake found that Chooseday's form rejected a sample roster despite visible names. Visimon generated multi-round schedules and an eight-person encounter matrix without an account. It was added with an editorial score of 4.1 and is currently rank 13; unverified capabilities remain marked conservatively.

## Targeted corrections

- **GroupMixer:** A six-person anonymous solve succeeded. Current pricing limits advanced generation: a verified free account gets three advanced generations per UTC day; Pro removes that allowance. The dataset now describes that gate, lowers account friction from 5.0 to 4.3, marks gated partial attendance and per-session capacity changes as `partial`, and records the presentation mode advertised in the current plan. Overall score remains 4.7 because the small solve did not establish a change in assignment quality.
- **Smart Group Maker:** The no-account app generated random and two-type balanced sample groups and honored a fixed placement. CSV results and a JSON scenario export downloaded successfully. The editor exposed together/apart controls, but their solver behavior was not verified, so the relationship flags remain `partial`. The dataset increases the features and outputs category scores; the overall score remains 3.8.
- **Visimon:** An eight-person sample generated multiple breakout rounds, repeat reporting, and an encounter matrix without signup. The new entry is scored 4.1 overall. File result exports and larger optimization cases remain unverified.

## Full queue resolution

| Availability or access item | 2026-09-22 outcome |
|---|---|
| 1000tools Random Pairs Generator | Live URL is a parked domain with no generator. Moved from the ranked list to `data/reviewed-out-of-scope.json`; no replacement URL found. |
| LessonKind Group Maker | The old route and the site's own homepage link redirect to a tools index without Group Maker. Moved to the out-of-scope record until a working route returns. |
| Wordwall resource | Live as a fixed Spin the wheel activity. Retained at its low score with an updated availability note; no ad-hoc roster/team-size workflow was found. |
| DateRounds and FastRounds | Current free-host pages still state a six-attendee cap; paid pages state unlimited attendees. Fresh free-host submissions were throttled, so the earlier dashboard observations were not repeated. Pricing and scores stay unchanged. |
| Begoodtool Smart Grouping Tool | Seven names into three groups produced 3/3/1 within the displayed `2 ±1` tolerance. The earlier 12-person 5/5/2 miss remains; the conservative result-quality score stays. |
| RemagineAI Random Group Generator | The public page claims no login, but its Get Started path led to `/auth` with no public generator. Retained only as a very low-rated entry with an updated note. |

| Feature check | 2026-09-22 outcome |
|---|---|
| RandomSelect | Feasible together/apart pairs were honored in two runs. The site labels these rules best effort; soft preference flags are `yes`, hard flags remain `no`. |
| ToolV | A Cloudflare human-verification challenge blocked the browser test. Image export remains unverified and its flag stays `no`. |
| TheToolApp | First-party client code implements `teams.png`, but two live input attempts did not render a result or file. Image export is `partial`, with the failed workflow noted. |
| CodersTool | Feasible pairs were honored once, but a conflicting together/apart pair silently broke together, and a 6-person split was 4/2 when 3/3 was feasible. Soft preference flags are `partial`; hard flags remain `no`. |
| Stilest | Six names generated teams, with Regenerate and Copy Teams but no CSV control. CSV remains `no` despite page export copy. |
| FateFactory | Generated sample teams and downloaded a valid PNG; no CSV control appeared. Image export is `yes`, CSV remains `no`. |
| LetsRandomize | Generated teams and exposed Copy CSV. First-party code copies CSV text to the clipboard rather than downloading a file, so CSV export is `partial`. |
| ClassTools24 | Generated groups and downloaded a valid CSV with `Group,Name,Leader` columns; CSV is `yes`. |
| FateWheel | Downloaded a valid CSV with `Team,Member,Leader` columns and a valid PNG; both flags are `yes`. |
| SpinOfLuck | Followed the guide's Generate Teams link, generated two teams, and downloaded a valid CSV and PNG; both flags are `yes`. |

| Market candidate | 2026-09-22 outcome |
|---|---|
| Chooseday | Two live input formats again failed with “Enter at least 2 names” despite visible names. Recorded as broken in `data/reviewed-out-of-scope.json`; revisit if repaired. |
| TeamCreator | Added at rank 5, overall 4.3. An explicit-header roster generated complete teams. A 12-person two-round sample honored together and apart pairs in both rounds, and a private assignment CSV downloaded. Bare one-column input treats the first row as a header. |
| TeamShuffler | Added at rank 77, overall 3.7. Free six-person generation worked; differentiating Pro claims remain gated and mostly untested. |
| Random Wheel Tools Multi-Round Group Generator | Added at rank 30, overall 4.0. A 12-person four-round sample and plain-text schedule download worked; it reported repeat encounters. |

The catalog edits were made directly in `data/tools.json`. Reconcile them with the review-builder source before running `scripts/import_review_builder_json.py` again; importing an older draft would overwrite these corrections and new entries. ToolV access and TheToolApp's live generation remain unresolved; the catalog flags reflect that limit.
