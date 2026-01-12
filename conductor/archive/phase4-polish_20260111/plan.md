# Developer Experience - Plan [checkpoint: e821a8c]

## Goal
Improve usability and maintainability.

## Tasks

### 4.1 CLI Runner
- [x] Create `cli.py` with `argparse` interface (738b19d)
- [x] Support `--bbox`, `--resolution`, `--year`, `--output-dir` (738b19d)
- [x] Output summary JSON with paths to cached files (738b19d)

### 4.2 Standalone Visualization
- [x] Create `preview.py` using `matplotlib` (74fda8b)
- [x] Support previewing elevation, embeddings (PCA), OSM overlay (74fda8b)
- [x] Useful for debugging without Houdini (74fda8b)

### 4.3 Type Hints & Documentation
- [x] Add type hints to all public functions (c2c75f5)
- [x] Add docstrings following Google style (c2c75f5)
- [x] Run `mypy` in strict mode, fix errors (c2c75f5)

## Files to Modify
| Action | File |
|--------|------|
| NEW | `python/deep_earth/cli.py` |
| NEW | `python/deep_earth/__main__.py` |
| NEW | `python/deep_earth/preview.py` |
| MODIFY | `pyproject.toml` |
| MODIFY | All Python files (type hints) |

## Verification
```bash
python -m deep_earth --help
python -m deep_earth --bbox 44.97,-93.28,44.99,-93.25 --resolution 10
mypy python/deep_earth --strict
```
