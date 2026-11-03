# Golden evals

Schema validation proves a model returned the right *shape*. Golden evals check it returned the right *answer*.

Each file in [`evals/golden/`](https://github.com/pratsy/B2B_agent_skills/tree/main/evals/golden) holds cases for one skill: realistic input and assertions on what the methodology must produce. For example, `forecast-confidence-model` must classify a MEDDPICC-20 deal as Best Case when time-in-stage is 1.89× the median and the rep's commit accuracy is 55%:

```json
{
  "id": "qualified-but-stalled",
  "input": {"meddpicc_score": 20, "days_in_current_stage": 34, "historical_median_days_in_stage": {"negotiation": 18}, "...": "..."},
  "assertions": [
    {"path": "time_in_stage_ratio", "approx": 1.89, "tol": 0.02},
    {"path": "checks.rep_calibration_pass", "equals": false},
    {"path": "forecast_category", "equals": "best case"}
  ]
}
```

## Run them

```bash
b2b-skills eval --provider claude-code --concurrency 4        # all cases, via your Claude subscription
b2b-skills eval --provider anthropic                          # all cases, via the API
b2b-skills eval --provider anthropic --skill deal-risk-assessor
b2b-skills eval --provider openai --model gpt-4o --json report.json --min-pass-rate 0.8
```

No API key? `b2b-skills eval --provider claude-code --concurrency 4` runs the suite through your local Claude Code login (including a Claude subscription).

In GitHub, run **Actions → Golden evals (real model) → Run workflow**. The default `claude-code` provider runs on your Claude subscription: create a token once with `claude setup-token` and save it as the `CLAUDE_CODE_OAUTH_TOKEN` repository secret. Choose `anthropic` or `openai` to use an API key secret instead. It's manual because it uses model quota, and it posts a results table to the job summary.

## What CI checks without a model

Cases marked `"readme_example": true` mirror a README's worked example. CI checks that the README's documented output passes those assertions, so the README and the golden case can't drift apart. Every case is also checked for being well-formed.

## Assertion reference

| Op | Passes when |
|---|---|
| `equals` | exact match. Strings ignore case, spaces, `_` and `-` (`"Best Case"` = `"best_case"`) |
| `approx` + `tol` | number within `tol` (default 1% of expected) |
| `one_of` | equals any listed value |
| `contains` | substring of a string, or member of a list |
| `matches` | regex search on a string, case-insensitive |
| `gte` / `lte` | numeric bound |
| `length` | list or string length |

Paths: `checks.time_in_stage_pass`, `themes[0].name`, and `accounts_ranked[account_id=acct_B].tier` (select a list item by field, independent of order).

## Writing a good case

- Make the evidence **unambiguous under the rubric**. The case should test the method, not how the model reads vague notes.
- Assert the **decision** (band, category, routing) and the **key numbers**, with tolerances that match the method's precision.
- Add a **contrast case** that flips the decision (e.g. same fit, no intent → nurture instead of rep call). Contrast cases catch models that pattern-match the example.
- Use `why` on an assertion to explain the rubric step, so a failure explains itself.

All 46 skills have golden suites (60 cases). Contrast cases and band-boundary cases for skills that have only one case are good first contributions.
