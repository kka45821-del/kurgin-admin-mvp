from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.core.config import get_settings
from packages.cvdlab_core.contracts.public_catalog import build_public_catalog_snapshot
from packages.cvdlab_core.contracts.public_index import PublicIndexRow, build_public_index_snapshot
from packages.cvdlab_core.contracts.site_settings import build_site_settings_snapshot

settings = get_settings()
app = FastAPI(title="CVDLAB Platform API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_site_url, settings.admin_url, "http://localhost:8501", "http://localhost:8502"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}

@app.get("/catalog/public-snapshot")
def public_catalog_snapshot():
    return build_public_catalog_snapshot([])

@app.get("/index/public-snapshot")
def public_index_snapshot():
    rows = [PublicIndexRow("D", "VS1", 1.0, 1.5, "standard", "Standard", 780000)]
    return build_public_index_snapshot(rows, active_index_version="demo_index_v1")

@app.get("/site-settings/snapshot")
def site_settings_snapshot():
    return build_site_settings_snapshot()
