# Core Stability - Specification

## Logging Infrastructure

### Environment Variable
`DEEP_EARTH_LOG_LEVEL` - Valid values: DEBUG, INFO, WARNING, ERROR

### Log Format
```
%(asctime)s [%(name)s] %(levelname)s: %(message)s
```

### Log Events
| Event | Level | Message |
|-------|-------|---------|
| Fetch start | INFO | `Fetching {provider} for bbox {bbox}` |
| Cache hit | DEBUG | `Cache hit for {key}` |
| Cache miss | DEBUG | `Cache miss for {key}` |
| Fetch complete | INFO | `Fetched {provider} in {duration}s` |
| Retry attempt | WARNING | `Retry {n}/3 for {url}` |
| Error | ERROR | `{provider} failed: {error}` |

---

## Retry Logic

### Configuration
- Max attempts: 3
- Wait: exponential (2s, 4s, 8s)
- Retry on: `aiohttp.ClientError`, status 429, status 5xx

### Implementation
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
async def fetch_with_retry(session, url, **kwargs):
    ...
```

---

## Cache TTL

| Category | TTL | Rationale |
|----------|-----|-----------|
| SRTM | Never | Static dataset |
| Embeddings | 365 days | Annual updates |
| OSM | 30 days | Frequent updates |

### Metadata Schema
```json
{
  "version": "1.0",
  "entries": {
    "key": {"created": "ISO8601", "ttl_days": 30}
  }
}
```
