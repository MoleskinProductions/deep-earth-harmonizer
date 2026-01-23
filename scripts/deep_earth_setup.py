#!/usr/bin/env python3
"""
Deep Earth Harmonizer - Setup Wizard (Standalone Script)

This script can be run directly without installing the package.
For installed usage, use: deep-earth setup
"""

import os
import sys

# Add parent directory to path for standalone usage
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
python_path = os.path.join(project_root, "python")
if python_path not in sys.path:
    sys.path.insert(0, python_path)

from deep_earth.setup_wizard import setup_wizard

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deep Earth Harmonizer Setup Wizard")
    parser.add_argument("--generate-template", action="store_true",
                        help="Generate template files without prompts")
    parser.add_argument("--output", "-o", type=str,
                        help="Output path for generated files")
    args = parser.parse_args()

    setup_wizard(
        generate_template=args.generate_template,
        output_path=args.output
    )
