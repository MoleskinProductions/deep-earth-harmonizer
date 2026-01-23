# Deep Earth Credentials Setup

## Overview

Deep Earth Harmonizer requires API credentials for:
- **Google Earth Engine** - Satellite embeddings
- **OpenTopography** - SRTM elevation data

## Quick Setup

Run the setup wizard to check your credential status:

```bash
deep-earth setup
```

## Configuration Methods

### Option 1: Environment Variables (Recommended)

```bash
# Earth Engine
export DEEP_EARTH_GEE_SERVICE_ACCOUNT="your-project@appspot.gserviceaccount.com"
export DEEP_EARTH_GEE_KEY_PATH="/path/to/service-account-key.json"

# OpenTopography
export DEEP_EARTH_OPENTOPO_KEY="your-api-key"
```

Add to your shell profile (`~/.bashrc`, `~/.zshrc`) for persistence.

### Option 2: Houdini Package JSON

Include credentials in your Houdini package file (`~/houdini21.0/packages/deep_earth.json`):

```json
{
    "env": [
        {
            "DEEP_EARTH_ROOT": "/path/to/planet_embeddings"
        },
        {
            "PYTHONPATH": {
                "value": ["$DEEP_EARTH_ROOT/python"],
                "method": "prepend"
            }
        },
        {
            "DEEP_EARTH_GEE_SERVICE_ACCOUNT": "your@email.com",
            "DEEP_EARTH_GEE_KEY_PATH": "/path/to/key.json",
            "DEEP_EARTH_OPENTOPO_KEY": "your_api_key"
        }
    ],
    "hpath": "$DEEP_EARTH_ROOT"
}
```

### Option 3: Credentials File

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
2. Create a new project or select an existing one
3. Enable the **Earth Engine API**:
   - Go to APIs & Services > Library
   - Search for "Earth Engine"
   - Click Enable
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Name it (e.g., "deep-earth-harmonizer")
   - Grant role: "Earth Engine Resource Viewer" (or custom)
5. Create and download a JSON key:
   - Click on the service account
   - Go to Keys tab
   - Add Key > Create new key > JSON
   - Save the downloaded file securely

### OpenTopography

1. Register at [OpenTopography](https://portal.opentopography.org/)
2. Log in and go to MyOpenTopo (user menu)
3. Click "Request API Key"
4. Copy the generated key

## Testing Your Credentials

### Using the Setup Wizard

```bash
deep-earth setup
```

Look for the credential status output:

```
[1/4] Checking Credentials...
----------------------------------------
  Earth Engine:   OK
    Key file: /path/to/key.json (exists)
  OpenTopography: OK
```

### Using the CLI

Test a small fetch:

```bash
deep-earth fetch --bbox 44.97,-93.27,44.975,-93.265 --resolution 30
```

Check the output for errors:
- "Earth Engine authentication failed" - GEE credentials issue
- "OpenTopography 401" - Invalid API key

### Programmatic Validation

```python
from deep_earth.credentials import CredentialsManager

creds = CredentialsManager()
status = creds.validate()
print(f"Earth Engine: {status['earth_engine']}")
print(f"OpenTopography: {status['opentopography']}")
```

## Troubleshooting

### "Earth Engine authentication failed"

**Causes:**
- Service account email is incorrect
- Key file path is wrong or file doesn't exist
- Earth Engine API not enabled for the project
- Service account lacks permissions

**Solutions:**
1. Verify the key file exists: `ls -la $DEEP_EARTH_GEE_KEY_PATH`
2. Check the service account email matches the key file
3. Verify Earth Engine API is enabled in Cloud Console
4. Try authenticating manually:
   ```python
   import ee
   credentials = ee.ServiceAccountCredentials(
       'your-account@project.iam.gserviceaccount.com',
       '/path/to/key.json'
   )
   ee.Initialize(credentials)
   ```

### "OpenTopography 401 Unauthorized"

**Causes:**
- API key is invalid or expired
- Key not set in environment

**Solutions:**
1. Verify the key is set: `echo $DEEP_EARTH_OPENTOPO_KEY`
2. Generate a new key at opentopography.org if needed
3. Check for extra whitespace in the key value

### "ModuleNotFoundError" when importing credentials

- Ensure deep_earth is installed: `pip install -e .`
- Check PYTHONPATH includes the package

### Credentials work in terminal but not in Houdini

- Environment variables may not propagate to Houdini
- Add credentials to the Houdini package JSON instead
- Or source your shell profile before launching Houdini

## Security Notes

> **NEVER commit credential files to version control!**

The `.gitignore` already excludes common credential patterns:
- `*.json` key files
- `credentials.json`
- `.env` files

Best practices:
- Store key files outside the repository
- Use environment variables in CI/CD
- Rotate keys periodically
- Use minimal permissions for service accounts

## Links

- [Earth Engine Service Accounts](https://developers.google.com/earth-engine/guides/service_account)
- [OpenTopography API Documentation](https://portal.opentopography.org/apidocs/)
- [Setup Wizard](../README.md#quick-install)
