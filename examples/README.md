# Examples

Sample inputs in [`fixtures/`](fixtures/), each matching the inputs a skill documents:

| File | Skill |
|---|---|
| `deal_risk_input.json` | `deal-risk-assessor` |
| `pipeline_input.json` | `pipeline-health-monitor` |
| `renewal_input.json` | `renewal-risk-scorer` |
| `audience_segmentation_input.json` | `audience-segmentation-optimizer` |
| `brand_positioning_input.json` | `brand-positioning-synthesizer` |
| `nurture_sequence_input.json` | `nurture-sequence-architect` |

```bash
# offline: returns the README's worked-example output
b2b-skills run deal-risk-assessor -i examples/fixtures/deal_risk_input.json

# real model
b2b-skills run deal-risk-assessor -i examples/fixtures/deal_risk_input.json --provider anthropic
```

In Python:

```python
from b2b_agent_skills import run_skill

result = run_skill("pipeline-health-monitor", "examples/fixtures/pipeline_input.json", provider="anthropic")
print(result.output["overall_health"], "-", result.output["primary_driver"])
```

For an HTTP service, use the built-in server (`b2b-skills serve`, see [docs/http-api.md](../docs/http-api.md)) rather than writing your own.
