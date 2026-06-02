from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from kurgin.data_io import load_sample_catalog
from kurgin.formula import score_catalog


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ok = compileall.compile_dir(root / "kurgin", quiet=1)
    ok = compileall.compile_file(root / "app.py", quiet=1) and ok
    ok = compileall.compile_dir(root / "pages", quiet=1) and ok
    if not ok:
        raise SystemExit("Compilation failed")

    sample = load_sample_catalog()
    scored = score_catalog(sample)
    assert not scored.empty
    assert scored["kurgin_score"].between(0, 100).all()
    assert "price_per_carat" in scored.columns
    print("KURGIN validation OK")


if __name__ == "__main__":
    main()
