# Deep Earth Credentials Setup

## Overview

Deep Earth Harmonizer requires API credentials for:
- **Google Earth Engine** — Satellite embeddings
- **OpenTopography** — SRTM elevation data

## Configuration Methods

### Option 1: Environment Variables (Recommended for CI/Production)

```bash
# Earth Engine
export DEEP_EARTH_GEE_SERVICE_ACCOUNT="your-project@appspot.gserviceaccount.com"
export DEEP_EARTH_GEE_KEY_PATH="/path/to/service-account-key.json"

# OpenTopography
export DEEP_EARTH_OPENTOPO_KEY="your-api-key"
```

### Option 2: Credentials File

Create `$HOUDINI_USER_PREF_DIR/deep_earth/credentials.json`:

```json
{
  "earth_engine": {
    "service_account": "your-project@appspot.gserviceaccount.com",
    "key_file": "/path/to/service-account-key.json"
  },
  "opentopography": {
    "api_key": "your-api-key"
  }
}
```

You can also set `DEEP_EARTH_CREDENTIALS_PATH` to use a custom location.

## Getting Credentials

### Google Earth Engine
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a service account with Earth Engine API access
3. Download the JSON key file
4. Enable Earth Engine API for your project

### OpenTopography
1. Register at [OpenTopography](https://portal.opentopography.org/)
2. Generate an API key from your profile

## Security Notes

> ⚠️ **NEVER commit credential files to version control!**

The `.gitignore` already excludes common credential patterns. Keep your key files outside the repository.
