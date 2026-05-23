"""Local disk path helpers (no storage.client import — safe for Settings validators)."""

from pathlib import Path


def api_app_root() -> Path:
    """Directory containing the API package (`apps/api`)."""
    return Path(__file__).resolve().parents[2]


def resolve_storage_local_path(path: str, *, base: Path | None = None) -> Path:
    """
    Turn STORAGE_LOCAL_PATH into an absolute directory.

    Relative values (e.g. `./uploads`) resolve against `apps/api`, not shell CWD.
    """
    raw = Path((path or './uploads').strip())
    if raw.is_absolute():
        return raw.resolve()
    anchor = base or api_app_root()
    return (anchor / raw).resolve()
