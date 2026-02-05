# Installation Guide

## Prerequisites

- **Python 3.9+** (3.11 recommended for Houdini compatibility)
- **Houdini 21.0+** (for HDA usage)
- **Git** (to clone the repository)

## Step 1: Install the Python Package

### From source (development mode)

```bash
git clone https://github.com/deep-earth/deep-earth-harmonizer.git
cd deep-earth-harmonizer
pip install -e .
```

### From wheel

```bash
pip install deep_earth-0.2.0-py3-none-any.whl
```

### Optional: preview support

```bash
pip install "deep_earth[preview]"
```

Verify the installation:

```bash
deep-earth --help
```

## Step 2: Configure Credentials

Deep Earth requires API keys for data providers:

### Google Earth Engine

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable the **Earth Engine API**
4. Create a service account with Earth Engine access
5. Download the JSON key file

### OpenTopography

1. Register at [OpenTopography](https://portal.opentopography.org/)
2. Go to your profile and generate an API key

### Set Environment Variables

```bash
export DEEP_EARTH_GEE_SERVICE_ACCOUNT="your-account@your-project.iam.gserviceaccount.com"
export DEEP_EARTH_GEE_KEY_PATH="/path/to/service-account-key.json"
export DEEP_EARTH_OPENTOPO_KEY="your-api-key"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`) for persistence.

See [CREDENTIALS.md](CREDENTIALS.md) for detailed credential setup instructions.

## Step 3: Run the Setup Wizard

```bash
deep-earth setup
```

The wizard will:
- Verify your credentials are configured
- Show your cache path
- Offer to create the Houdini package configuration

## Step 4: Configure Houdini

The setup wizard can create the package file automatically. To do it manually:

Create `~/houdini21.0/packages/deep_earth.json`:

```json
{
    "env": [
        {
            "DEEP_EARTH_ROOT": "/path/to/deep-earth-harmonizer"
        },
        {
            "PYTHONPATH": {
                "value": ["$DEEP_EARTH_ROOT/python"],
                "method": "prepend"
            }
        },
        {
            "DEEP_EARTH_GEE_SERVICE_ACCOUNT": "your-account@project.iam.gserviceaccount.com",
            "DEEP_EARTH_GEE_KEY_PATH": "/path/to/service-account-key.json",
            "DEEP_EARTH_OPENTOPO_KEY": "your-api-key"
        }
    ],
    "hpath": "$DEEP_EARTH_ROOT"
}
```

Replace `/path/to/deep-earth-harmonizer` with your actual installation path.

A distributable template is provided at `planet_embeddings.json.template`.

## Step 5: Verify Installation

### CLI Verification

```bash
deep-earth fetch --bbox 44.97,-93.27,44.98,-93.26 --resolution 10
```

Expected output: JSON with `results` (provider paths) and optional `errors`.

### Houdini Verification

1. Start Houdini
2. Create a Geometry node
3. Inside, Tab-search for "Deep Earth Harmonizer"
4. Drop the node and click **Fetch Data**

## Troubleshooting

### "ModuleNotFoundError: No module named 'deep_earth'"

- Check that PYTHONPATH includes the `python` directory
- Verify the package JSON is in `~/houdini21.0/packages/`
- Restart Houdini after changing package files

### "Earth Engine authentication failed"

- Verify DEEP_EARTH_GEE_KEY_PATH points to a valid JSON file
- Check the service account has Earth Engine API access
- Run `deep-earth setup` to validate credentials

### "OpenTopography 401 Unauthorized"

- Verify DEEP_EARTH_OPENTOPO_KEY is set correctly
- Check your API key is valid at opentopography.org

### Cache Issues

Clear the cache if data seems stale:

```bash
rm -rf ~/.deep_earth_cache
```

Or check your configured cache path:

```bash
deep-earth setup  # Shows current cache path
```

## Next Steps

- Follow the [Quick Start Guide](QUICKSTART.md) to fetch your first data
- Review [CREDENTIALS.md](CREDENTIALS.md) for advanced credential options
