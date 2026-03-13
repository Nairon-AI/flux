#!/usr/bin/env python3
"""
fluxctl - CLI for managing .flux/ task tracking system.

Thin wrapper that delegates to the fluxctl_pkg package.
"""
import sys
import os

# Ensure the scripts directory is on the path so fluxctl_pkg is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fluxctl_pkg.__main__ import main

if __name__ == "__main__":
    main()
