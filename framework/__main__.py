"""Allow ``python -m framework`` to invoke the CLI."""

from framework.cli import main

if __name__ == "__main__":
    raise SystemExit(main())