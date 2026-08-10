from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    text = payload.get("input")
    success = isinstance(text, str) and text.startswith(("Refund ", "Cancel "))
    print(json.dumps({"success": success}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
