# Security

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/pratsy/skills-AI/security/advisories/new). Please don't open a public issue. Include what's affected (SDK, CLI, MCP server, HTTP server, plugin), how to reproduce it, and the impact you expect. You'll get an acknowledgement within 5 business days, and the fix and disclosure timeline will be agreed with you.

Supported versions: the latest release on PyPI. Fixes are not backported.

**In scope:** the `b2b_agent_skills` package (SDK, CLI, MCP server, HTTP server), the Docker image, the Claude Code plugin manifests, and the GitHub workflows.
**Out of scope:** a model's answer quality or a skill giving bad business advice (open a regular issue), and vulnerabilities in your own deployment's infrastructure.

## What leaves your machine

Running a skill with a real provider sends two things to that provider: the skill's instructions and output schema (public, committed here) and **your input data, verbatim**. Nothing in this package redacts input. Treat every call as "this JSON goes to a third-party API".

- `PROVIDER=mock` (the default) makes no network calls.
- The MCP server's `list_skills`, `get_skill`, and prompts send nothing anywhere. Your MCP client's own model does the work. The `run_skill` tool exists only when you set `PROVIDER=anthropic|openai`.
- The Claude Code plugin is markdown and JSON only. It runs no code.

Before passing real account or customer data:

- Send only the fields the skill documents as inputs. A deal-risk score doesn't need the contract text.
- Never include credentials, internal system IDs, or personal data the analysis doesn't need.
- Check your provider's data-retention and training-use terms for your API tier.

## Credentials

Provider keys are read only from the environment (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or anything else the official SDKs resolve), never from skill files or function defaults. `.env` is git-ignored. Don't commit one.

**Don't embed tokens in git remote URLs** (`https://user:TOKEN@github.com/...`). They're stored in plain text in `.git/config` and show up in `git remote -v`. Use `gh auth login` or your OS credential helper.

## Running the HTTP server

`b2b-skills serve` is built to be safe by default:

- It requires a bearer token (`B2B_SKILLS_API_TOKEN`), compared in constant time. It refuses to start without one unless `B2B_SKILLS_ALLOW_NO_AUTH=1` is set (for local development only).
- Request bodies are capped (`B2B_SKILLS_MAX_BODY_BYTES`, default 256 KB).
- Error responses never include provider error messages or stack traces.
- The Docker image runs as a non-root user.

You are responsible for TLS termination and rate limiting in front of it. Every request costs model tokens, so an unthrottled public endpoint is a cost risk even with authentication.

## Prompt injection

Skill inputs often contain text from outside your organization: emails, call transcripts, competitor pages. That text can contain instructions aimed at the model. Structured outputs and schema validation limit what a manipulated response can look like (it must still match the skill's schema), but they can't guarantee the values are honest. Don't let skill output trigger irreversible actions (sending emails, changing CRM stages) without a human or rule-based check.
