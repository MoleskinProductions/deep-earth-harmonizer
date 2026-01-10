# Developer Experience - Plan

## Goal
Improve usability and maintainability.

## Tasks

### 4.1 CLI Runner
- [ ] Create `cli.py` with `argparse` interface
- [ ] Support `--bbox`, `--resolution`, `--year`, `--output-dir`
- [ ] Output summary JSON with paths to cached files

### 4.2 Standalone Visualization
- [ ] Create `preview.py` using `matplotlib`
- [ ] Support previewing elevation, embeddings (PCA), OSM overlay
- [ ] Useful for debugging without Houdini

### 4.3 Type Hints & Documentation
- [ ] Add type hints to all public functions
- [ ] Add docstrings following Google style
- [ ] Run `mypy` in strict mode, fix errors

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
