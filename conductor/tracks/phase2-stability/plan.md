# Core Stability - Plan

## Goal
Make the system robust and debuggable.

## Tasks

### 2.1 Logging Infrastructure
- [x] Create `logging_config.py` with file + console handlers
- [~] Add logging to all providers (fetch start/end, cache hits, errors)
- [ ] Respect `DEEP_EARTH_LOG_LEVEL` environment variable

### 2.2 Retry Logic
- [ ] Add `tenacity>=8.0` to dependencies
- [ ] Wrap HTTP calls in retry decorator (max 3 attempts, exponential backoff)
- [ ] Handle 429 (rate limit) with longer wait

### 2.3 Enhanced Cache
- [ ] Add TTL support (SRTM=never, OSM=30 days)
- [ ] Add `cache_metadata.json` tracking version, timestamps
- [ ] Add `invalidate(key)` and `clear_stale()` methods
- [ ] Add cache corruption detection

## Files to Modify
| Action | File |
|--------|------|
| NEW | `python/deep_earth/logging_config.py` |
| NEW | `python/deep_earth/retry.py` |
| MODIFY | `python/deep_earth/cache.py` |
| MODIFY | `python/deep_earth/providers/srtm.py` |
| MODIFY | `python/deep_earth/providers/earth_engine.py` |
| MODIFY | `python/deep_earth/providers/osm.py` |
| MODIFY | `pyproject.toml` |

## Verification
```bash
pytest tests/test_cache.py tests/test_srtm.py tests/test_osm.py -v
DEEP_EARTH_LOG_LEVEL=DEBUG python -c "from deep_earth.logging_config import setup_logging; setup_logging()"
```
