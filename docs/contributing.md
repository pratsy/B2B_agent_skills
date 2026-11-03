# Contributing

See [CONTRIBUTING.md](https://github.com/pratsy/B2B_agent_skills/blob/main/CONTRIBUTING.md) for the full guide. In short:

```bash
git clone https://github.com/pratsy/B2B_agent_skills && cd B2B_agent_skills
pip install -e ".[dev]"
pre-commit install
pytest
```

The most valuable contributions right now:

1. **More golden eval cases**: contrast and band-boundary cases (see [Golden evals](evals.md)).
2. **Skill quality fixes**: a scoring step that's ambiguous, a worked example whose numbers don't add up, a failure pattern that's missing.
3. **Real-model eval results**: run `b2b-skills eval` against a model and open an issue with the report.
