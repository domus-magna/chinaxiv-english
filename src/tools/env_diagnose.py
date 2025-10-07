#!/usr/bin/env python3
"""
Environment variable diagnostic and resolution tool.

This tool helps diagnose and resolve shell/.env mismatches that cause
API key issues in the ChinaXiv translation pipeline.
"""
import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.env_utils import detect_env_mismatches, resolve_env_mismatches, ensure_env_consistency, validate_api_key
from src.logging_utils import log


def main():
    parser = argparse.ArgumentParser(description="Diagnose and resolve environment variable issues")
    parser.add_argument("--check", action="store_true", help="Check for mismatches")
    parser.add_argument("--resolve", action="store_true", help="Resolve mismatches")
    parser.add_argument("--validate", action="store_true", help="Validate API keys")
    parser.add_argument("--keys", nargs="+", default=["OPENROUTER_API_KEY"], help="Keys to check")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    args = parser.parse_args()
    
    if not any([args.check, args.resolve, args.validate]):
        args.check = True  # Default to check mode
    
    log(f"Environment diagnostic tool - checking keys: {args.keys}")
    
    if args.check:
        log("=== CHECKING FOR MISMATCHES ===")
        mismatches = detect_env_mismatches(args.keys, args.env_file)
        
        if not mismatches:
            log("✅ No mismatches found - environment variables are consistent")
        else:
            log(f"❌ Found {len(mismatches)} mismatches:")
            for key, mismatch in mismatches.items():
                shell_val = mismatch['shell'][:20] + "..." if mismatch['shell'] else "None"
                file_val = mismatch['file'][:20] + "..." if mismatch['file'] else "None"
                log(f"  {key}:")
                log(f"    Shell: {shell_val}")
                log(f"    File:  {file_val}")
    
    if args.resolve:
        log("=== RESOLVING MISMATCHES ===")
        ensure_env_consistency(args.keys, args.env_file)
        log("✅ Mismatches resolved")
    
    if args.validate:
        log("=== VALIDATING API KEYS ===")
        for key in args.keys:
            if key.endswith("_API_KEY"):
                log(f"Validating {key}...")
                if validate_api_key(key):
                    log(f"✅ {key} is valid")
                else:
                    log(f"❌ {key} is invalid or expired")
            else:
                log(f"⚠️ Skipping {key} (not an API key)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
