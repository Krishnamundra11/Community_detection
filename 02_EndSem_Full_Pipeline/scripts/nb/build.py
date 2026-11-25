"""Assemble notebooks from cell-spec modules and (optionally) execute them.

Each spec module in _build/nb/specs/ exposes TITLE and CELLS, a list of ("md", text) / ("code", text).
Usage:
  python build.py                 # write all notebooks (no execution)
  python build.py 02 03 --run     # write + execute the listed notebooks in order
  python build.py --run           # write + execute everything in order
"""
import importlib.util
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NB_DIR = ROOT / "notebooks"
SPECS = sorted((HERE / "specs").glob("nb*.py"))


def load_spec(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assemble(mod, out_path: Path):
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "csma", "display_name": "Python (csma)", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    cells = []
    for kind, text in mod.CELLS:
        text = text.strip("\n")
        cells.append(nbformat.v4.new_markdown_cell(text) if kind == "md" else nbformat.v4.new_code_cell(text))
    nb.cells = cells
    nbformat.write(nb, out_path)


def execute(out_path: Path, timeout=7200):
    nb = nbformat.read(out_path, as_version=4)
    client = NotebookClient(nb, timeout=timeout, kernel_name="csma", resources={"metadata": {"path": str(NB_DIR)}},
                            allow_errors=False)
    t0 = time.time()
    try:
        client.execute()
    finally:
        nbformat.write(nb, out_path)      # keep partial outputs for debugging when a cell fails
    return time.time() - t0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run = "--run" in sys.argv
    for spec_path in SPECS:
        num = spec_path.stem[2:4]
        if args and num not in args:
            continue
        mod = load_spec(spec_path)
        out = NB_DIR / f"{mod.FILENAME}.ipynb"
        assemble(mod, out)
        print(f"written {out.name} ({len(mod.CELLS)} cells)", flush=True)
        if run:
            try:
                secs = execute(out)
                print(f"  executed {out.name} in {secs/60:.1f} min", flush=True)
            except Exception as e:  # keep the partially executed notebook for inspection
                print(f"  FAILED {out.name}: {type(e).__name__}: {str(e)[:1500]}", flush=True)
                sys.exit(1)
