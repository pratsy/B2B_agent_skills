# Release checklist

## Before tagging

- [ ] CI is green on `main`
- [ ] Golden evals run against a real model (Actions → *Golden evals (real model)*) and the pass rate is recorded in the release notes
- [ ] `__version__` in `b2b_agent_skills/__init__.py` and `version` in `.claude-plugin/plugin.json` are bumped to the same value
- [ ] `CHANGELOG.md` has a section for the new version (move items out of *Unreleased*)
- [ ] Breaking changes to any skill's output schema are called out (they break downstream pipelines)

## Tag and publish

```bash
git tag v0.X.Y && git push origin v0.X.Y
```

`release.yml` checks the tag matches both version fields, runs the tests, publishes to PyPI with trusted publishing, and creates the GitHub release.

## After release

- [ ] `pip install b2b-agent-skills==0.X.Y` works in a clean environment
- [ ] `/plugin marketplace update b2b-agent-skills` picks up the new plugin version
- [ ] Docs site shows the new version
