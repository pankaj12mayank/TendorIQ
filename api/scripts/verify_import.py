"""Exit 0 when the API app imports cleanly (run from api/: python scripts/verify_import.py)."""
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from src.main import app

assert app.title
print('OK', app.title)
