# Repeat-avoidance benchmark: TeamCreator and GroupMixer (2026-09-22)

This checks the publicly usable TeamCreator browser page against GroupMixer's public solver API on the same uniform, unconstrained group shapes. The [full synthetic schedules and independently counted metrics](../data/benchmarks/repeat-avoidance-2026-09-22.json) are versioned so each number can be checked from the assignments. TeamCreator's [published Python reference](https://github.com/Collaboration-ai/teamcreator-uwt/tree/4129776a38057426b4112d4bc4eca4d24dbb5c9f) was run separately to test the site's claim that its browser engine matches the reference.

## Protocol

- Rosters contain only `P00` through `Pnn`; each person must appear exactly once per round, with the specified number and size of groups. All 45 outputs passed these validity checks.
- No person constraints or participant attributes were supplied. TeamCreator used its default preset, with all eight sliders at zero. GroupMixer used `objective=squared` through its [public Social Golfer API](https://groupmixer.app/api), which reports a two-second solve limit under the free `free_auto_v1` policy.
- Both were run with seeds 7, 42, and 123. The products use different random-number implementations; equal seed numbers are repeated trials, not identical starting schedules.
- A **repeat** is one pair meeting after their first meeting. A pair meeting four times contributes three repeats. We counted pairs from the full output schedules, rather than trusting either product's own diagnostic.
- The lower bound is `max(0, total pair encounters − n(n−1)/2)`. It is necessary, but need not be attainable. For the first four shapes, GroupMixer's zero-repeat output itself proves zero is attainable.

## Results

| People | Groups × size | Rounds | Simple lower bound | TeamCreator browser repeats (seeds 7 / 42 / 123) | TeamCreator Python reference | GroupMixer public API |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | 3 × 3 | 4 | 0 | 14 / 15 / 13 | 0 / 0 / 0 | **0 / 0 / 0** |
| 12 | 4 × 3 | 4 | 0 | 15 / 15 / 14 | 0 / 0 / 0 | **0 / 0 / 0** |
| 16 | 4 × 4 | 5 | 0 | 37 / 42 / 43 | 8 / 8 / 8 | **0 / 0 / 0** |
| 20 | 5 × 4 | 5 | 0 | 40 / 43 / 39 | 9 / 7 / 5 | **0 / 0 / 0** |
| 12 | 4 × 3 | 6 | ≥6 | 28 / 28 / 26 | 9 / 9 / 10 | **7 / 7 / 7** |

The final GroupMixer case returned `time_limited` with a valid schedule, meaning the API reached its two-second budget. Seven repeats is an observed result, not a proof of optimum. All other GroupMixer calls returned `solved`. A fresh manual TeamCreator browser run at 9 people, three groups of three, four rounds, seed 42 reproduced 15 repeats. A downloaded browser CSV for 16 people, four groups of four, five rounds, seed 42 reproduced 42 repeats independently of DOM extraction.

## Why the implementations differ

The live page loaded [`teamcreator_engine.js?v=uwt-v2f-20260716`](https://unitedwetransform.com/teamcreator_engine.js?v=uwt-v2f-20260716), SHA-256 `64a2a178b8749335ced0670556ed794d723ba61617759e1b99c910194c65559a`. Its `createRounds` calls the same placement function for each round with a changed seed. Earlier pairings are passed into `createTeams`, but that function uses them for output scores, not for choosing team members. Its code also states that pairwise scores from the similarity sliders do not determine team membership. The [page's UI code](https://unitedwetransform.com/teamcreator_ui.js?v=uwt-v2f-20260716) calls this `createRounds` function. Thus the browser workflow produces independently seeded splits, rather than optimizing against the prior rounds.

As a separate check of the slider path, eight people with two organization labels were grouped with the organization slider at +5 and then −5 using the same seed. Team membership was identical in the two live browser results. This confirms the observed code path for that input; it is not a general benchmark of attribute balancing.

The Python reference at commit `4129776a38057426b4112d4bc4eca4d24dbb5c9f` uses a separate rotation engine with local swaps against prior pairings. It did better than the browser, but still missed known zero-repeat schedules at 16 and 20 people. The site's claim of byte-identical assignments between browser and Python did not hold for multi-round output: their first round matched in the 16-person seed-42 run, while later rounds and total repeats differed.

This is a narrow repeat-avoidance comparison. It does not test TeamCreator's richer roster fields, GroupMixer's scenario constraints, large instances, or solver runtime under equivalent hardware. The wall-clock times of a local Python CLI, a browser tab, and a hosted API are not directly comparable.
