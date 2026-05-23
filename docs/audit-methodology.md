# Audit methodology — E2E & root cause

Layer audits (L1–L35) track **code and contract fixes**. They are **not sufficient** for “project runs end-to-end” unless each layer also passes **reliability gates**.

## What “audit” means here

| Activity | Proves | Does not prove |
|----------|--------|----------------|
| Static layer test (`test_layerN_*.py` reads files) | File contains expected strings/patterns | App imports or serves traffic |
| Unit test with mocks | One function behaves | Full stack + DB + auth |
| **Reliability gate** (required for “done”) | Backend imports, health OK, critical paths reachable | Every edge case in production |

**Rule:** A layer is only **operationally complete** when its reliability gate passes (see [AUDIT_REPORT.md](../AUDIT_REPORT.md#system-reliability--root-causes)).

## Reliability gates (run every release / after large merges)

From repo root:

```powershell
# 1) API compiles
cd apps\api
.\venv\Scripts\python.exe -m compileall -q src

# 2) API imports (uses repo .env via DOTENV_PATH)
$env:DOTENV_PATH = "D:\Py_Projects\tendoriq\.env"   # adjust path
.\venv\Scripts\python.exe scripts\verify_import.py

# 3) Full local stack (MySQL must be running)
cd ..\..
.\scripts\tenderiq-start.ps1
# Expect: http://localhost:8000/health → healthy, http://localhost:3000 loads
```

Or use `run.bat` if that wraps the same script.

## Root-cause template

Every production-impacting issue in the audit report should be recorded as:

| Field | Meaning |
|-------|---------|
| **Symptom** | What the user saw (e.g. `Backend import check failed`) |
| **Root cause** | Why it happened (not the fix) |
| **Detection gap** | Why the layer audit missed it |
| **Fix** | Commit / file |
| **Gate** | Command that prevents recurrence |

## Why layer-only audits failed reliability

1. **No import gate** — `test_layer*.py` grep source; Python **syntax/import** errors only appear at `import app`.
2. **Wrong `.env` root** — `config.py` once resolved `apps/` instead of repo root → empty `DATABASE_URL` / `JWT_SECRET`.
3. **Stale venv** — `tenderiq-start.ps1` skipped `pip install` when venv existed → missing `svix` etc.
4. **Invalid FastAPI signatures** — `RequireX` deps after `Query(...)` defaults → `SyntaxError` at import.
5. **Corrupted / wrong imports** — e.g. `admin_auth.py` BOM/escaped quotes; SSO importing `permissions_for_role` from wrong module.

See the canonical table in [AUDIT_REPORT.md — System reliability & root causes](../AUDIT_REPORT.md#system-reliability--root-causes).
