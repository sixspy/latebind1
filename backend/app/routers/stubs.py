"""各功能题空桩：便于模型按题面定位；不是交表模板要求。"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/stubs", tags=["stubs"])

STUBS = (
    "bind_commit",
    "dim_version_pin",
    "quarantine_revive",
    "batch_cover_gate",
    "bindkey_fight",
    "dim_retire_gate",
    "fact_reingest_idem",
    "composite_bind_key",
    "reconcile_authority",
    "bind_run_cursor",
    "quarantine_batch_dispose",
    "bind_dry_run",
    "orphan_bound_cleanup",
    "bind_lock_scope",
    "ingest_during_bind",
)


@router.get("")
def list_stubs():
    return {"stubs": list(STUBS), "note": "未实现；按题面择一架构落地"}


@router.api_route("/{name}", methods=["GET", "POST", "PUT", "DELETE"])
def stub_hit(name: str):
    if name not in STUBS:
        raise HTTPException(404, f"unknown stub: {name}")
    raise HTTPException(
        501,
        detail={
            "stub": name,
            "implemented": False,
            "message": f"{name} 空桩未实现",
        },
    )
