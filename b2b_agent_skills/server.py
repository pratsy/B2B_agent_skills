"""HTTP API for running skills from other services.

    B2B_SKILLS_API_TOKEN=... PROVIDER=anthropic b2b-skills serve --host 0.0.0.0

Endpoints:
  GET  /health                 liveness, no auth
  GET  /v1/skills              list skills
  GET  /v1/skills/{name}       instructions + output schema
  POST /v1/skills/{name}/run   body: {"input": {...}} -> validated output

Every /v1 route requires ``Authorization: Bearer $B2B_SKILLS_API_TOKEN``. The
server refuses to start without a token unless ``B2B_SKILLS_ALLOW_NO_AUTH=1``
(for local development only). Requires the ``server`` extra.
"""

import hmac
import logging
import os
from typing import Any

from .errors import ProviderError, SkillNotFoundError, SkillOutputError
from .providers import get_provider
from .registry import get_skill, list_skills
from .runner import run_skill

logger = logging.getLogger("b2b_agent_skills.server")
MAX_BODY_BYTES = int(os.getenv("B2B_SKILLS_MAX_BODY_BYTES", str(256 * 1024)))


def create_app(token: str | None = None, provider: Any = None) -> Any:
    try:
        from fastapi import Depends, FastAPI, HTTPException, Request
        from fastapi.responses import JSONResponse
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from pydantic import BaseModel, Field
    except ImportError as e:  # pragma: no cover
        raise SystemExit("The HTTP server needs the server extra: pip install 'b2b-agent-skills[server]'") from e

    from . import __version__

    token = token if token is not None else os.getenv("B2B_SKILLS_API_TOKEN")
    if not token and os.getenv("B2B_SKILLS_ALLOW_NO_AUTH") != "1":
        raise RuntimeError("Set B2B_SKILLS_API_TOKEN (or B2B_SKILLS_ALLOW_NO_AUTH=1 for local development).")
    provider = provider or get_provider()

    app = FastAPI(title="B2B Agent Skills", version=__version__)
    bearer = HTTPBearer(auto_error=False)

    def require_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
        if not token:
            return
        if creds is None or not hmac.compare_digest(creds.credentials.encode(), token.encode()):
            raise HTTPException(status_code=401, detail="invalid or missing bearer token")

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next: Any) -> Any:
        length = request.headers.get("content-length")
        if length and int(length) > MAX_BODY_BYTES:
            return JSONResponse(status_code=413, content={"detail": f"request body exceeds {MAX_BODY_BYTES} bytes"})
        return await call_next(request)

    class RunRequest(BaseModel):
        input: dict[str, Any] = Field(..., description="Skill input data, as described in the skill's SKILL.md")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/skills", dependencies=[Depends(require_token)])
    def skills() -> list[dict[str, str]]:
        return [{"name": s, "description": get_skill(s).description} for s in list_skills()]

    @app.get("/v1/skills/{name}", dependencies=[Depends(require_token)])
    def skill(name: str) -> dict[str, Any]:
        try:
            s = get_skill(name)
        except SkillNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"name": s.name, "description": s.description, "instructions": s.instructions, "output_schema": s.output_schema}

    @app.post("/v1/skills/{name}/run", dependencies=[Depends(require_token)])
    def run(name: str, req: RunRequest) -> dict[str, Any]:
        try:
            result = run_skill(name, req.input, provider=provider)
        except SkillNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        except SkillOutputError as e:
            logger.warning("invalid model output for %s: %s", name, e.result.errors)
            raise HTTPException(
                status_code=502, detail={"message": "model output failed validation", "errors": e.result.errors[:10]}
            ) from e
        except ProviderError as e:
            logger.warning("provider error for %s: %s", name, e)
            raise HTTPException(status_code=502, detail="model provider error") from e
        return {
            "skill": result.skill,
            "output": result.output,
            "model": result.model,
            "usage": result.usage,
            "latency_ms": result.latency_ms,
        }

    return app


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)
