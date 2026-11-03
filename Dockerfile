# HTTP API server for B2B Agent Skills.
#
#   docker build -t b2b-agent-skills .
#   docker run -p 8000:8000 -e B2B_SKILLS_API_TOKEN=... -e PROVIDER=anthropic -e ANTHROPIC_API_KEY=... b2b-agent-skills
#
# Override the command to run the MCP server over HTTP instead:
#   docker run -p 8000:8000 b2b-agent-skills b2b-skills mcp --transport streamable-http

FROM python:3.12-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir build
COPY . .
RUN python -m build --wheel --outdir /dist

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build /dist/*.whl /tmp/
RUN WHEEL="$(ls /tmp/*.whl)" && pip install --no-cache-dir "${WHEEL}[anthropic,openai,server,mcp]" && rm /tmp/*.whl
RUN useradd --create-home --uid 10001 app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["b2b-skills", "serve", "--host", "0.0.0.0", "--port", "8000"]
