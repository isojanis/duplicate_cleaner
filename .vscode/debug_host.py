from __future__ import annotations

import runpy

import debugpy


def main() -> None:
    debugpy.listen(("127.0.0.1", 5678))
    print("debugpy-ready", flush=True)
    debugpy.wait_for_client()
    runpy.run_module("duplicate_cleaner", run_name="__main__")


if __name__ == "__main__":
    main()
