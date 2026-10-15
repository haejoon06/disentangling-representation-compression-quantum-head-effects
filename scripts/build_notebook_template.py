from pathlib import Path
import sys

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from article09.notebook import build_notebook


if __name__ == "__main__":
    output = ROOT / "notebooks" / "Article09_Reproducible_Research.ipynb"
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(build_notebook(), output)
    print(output)

