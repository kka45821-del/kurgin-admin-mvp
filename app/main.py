from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


SERVICE_NAME = "KURGIN Formula Service"
FORMULA_CONTRACT_VERSION = "v1/formula/stone"

bearer_scheme = HTTPBearer(auto_error=False)


class StoneEngineInput(BaseModel):
    crown_a: float = Field(..., description="Crown angle")
    pav_a: float = Field(..., description="Pavilion angle")
    table: float = Field(..., description="Table percentage")
    depth: float = Field(..., description="Depth percentage")
    crown_p: float = Field(..., description="Crown height percentage")
    pav_p: float = Field(..., description="Pavilion depth percentage")
    girdle_p: float = Field(..., description="Girdle percentage")


class FormulaStoneRequest(BaseModel):
    stone: StoneEngineInput


def settings() -> Dict[str, str]:
    return {
        "environment": os.getenv("KURGIN_FORMULA_ENV", "staging"),
        "service_version": os.getenv("KURGIN_FORMULA_SERVICE_VERSION", "0.1.0-staging"),
        "build_id": os.getenv("KURGIN_FORMULA_BUILD_ID", "local"),
        "api_key": os.getenv("KURGIN_FORMULA_API_KEY", ""),
    }


def version_payload() -> Dict[str, str]:
    current = settings()
    return {
        "service_name": SERVICE_NAME,
        "service_version": current["service_version"],
        "build_id": current["build_id"],
        "environment": current["environment"],
        "formula_contract_version": FORMULA_CONTRACT_VERSION,
    }


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> bool:
    expected = settings()["api_key"]
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Formula API key is not configured",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Formula API bearer token",
        )

    supplied = credentials.credentials.strip()
    if supplied != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Formula API bearer token",
        )
    return True


def calculate_formula(engine_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Load private formula at request time.

    In the real private repository, copy the private `core_formula/` and
    `config_settings/engine_config.py` next to this app. This scaffold avoids
    embedding formula code directly in this template.
    """
    try:
        from core_formula.main_engine import get_final_diamond_analysis
    except Exception as exc:
        raise RuntimeError("Private formula package is not installed in this service scaffold") from exc

    result = get_final_diamond_analysis(**engine_kwargs)
    required = [
        "engine_version",
        "final_score",
        "final_verdict",
        "triple_score",
        "structure_modifier",
        "structure_tags",
        "visual_check",
        "critical_risk",
        "diagnostics",
        "breakdown",
    ]
    missing = [field for field in required if field not in result]
    if missing:
        raise RuntimeError(f"Formula result missing required fields: {missing}")
    return result


app = FastAPI(
    title=SERVICE_NAME,
    version=settings()["service_version"],
    description="Private staging scaffold for KURGIN formula execution.",
)


@app.get("/v1/health")
def health():
    return {
        "status": "ok",
        "version": version_payload(),
    }


@app.get("/v1/ready")
def ready():
    sample = {
        "crown_a": 34.5,
        "pav_a": 40.8,
        "table": 56,
        "depth": 61.5,
        "crown_p": 15,
        "pav_p": 43,
        "girdle_p": 3.5,
    }
    try:
        result = calculate_formula(sample)
        ready_status = "ready" if result.get("final_score") is not None else "not_ready"
        return {
            "status": ready_status,
            "engine_version": result.get("engine_version"),
            "version": version_payload(),
        }
    except Exception as exc:
        return {
            "status": "not_ready",
            "error": str(exc),
            "version": version_payload(),
        }


@app.post("/v1/formula/stone", dependencies=[Depends(require_api_key)])
def formula_stone(payload: FormulaStoneRequest):
    try:
        engine_kwargs = payload.stone.model_dump()
        return calculate_formula(engine_kwargs)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
