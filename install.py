#!/usr/bin/env python3
"""
Antigravity Rules Presets Installer
Usage: python install.py <preset-name> [--target /path/to/project]
"""

import sys
import os
import shutil

AVAILABLE_PRESETS = [
    "nextjs-supabase",
    "express-playwright-scraping",
    "react-native-expo",
    "fastapi-postgresql",
    "go-gin-htmx",
    "langchain-langgraph-agent",
    "solana-anchor-rust"
]

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Antigravity Rules Presets Installer")
        print("\nAvailable presets:")
        for p in AVAILABLE_PRESETS:
            print(f"  - {p}")
        print("\nUsage:")
        print("  python install.py <preset-name> [--target /path/to/project]")
        sys.exit(0)

    preset = sys.argv[1]
    if preset not in AVAILABLE_PRESETS:
        print(f"Error: Unknown preset '{preset}'.")
        print(f"Choose from: {', '.join(AVAILABLE_PRESETS)}")
        sys.exit(1)

    target_dir = os.getcwd()
    if "--target" in sys.argv:
        idx = sys.argv.index("--target")
        if idx + 1 < len(sys.argv):
            target_dir = sys.argv[idx + 1]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_rules = os.path.join(script_dir, "presets", preset, "GEMINI.md")

    if not os.path.exists(source_rules):
        print(f"Error: Source rules file not found at {source_rules}")
        sys.exit(1)

    dest_dir = os.path.join(target_dir, ".gemini")
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, "GEMINI.md")

    shutil.copyfile(source_rules, dest_file)
    print(f"[OK] Installed '{preset}' rules to {dest_file}")
    print("Google Antigravity is now configured with battle-tested production defaults.")

if __name__ == "__main__":
    main()
