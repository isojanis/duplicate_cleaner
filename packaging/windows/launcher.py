"""Absolute import entry point for the frozen executable."""
from duplicate_cleaner.app import main

if __name__ == "__main__":
    raise SystemExit(main())
