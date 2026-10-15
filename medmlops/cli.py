"""Cross-platform reproducible workflows."""
import argparse
import json
import os
import sys
from pathlib import Path

from .data import generate, validate
from .model import drift, predict
from .store import Store
from .train import train


def main(argv=None):
    parser = argparse.ArgumentParser(description="MedMLOps synthetic research platform")
    parser.add_argument("--root", default=os.environ.get("MEDMLOPS_ROOT", "runtime"))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("train", "demo"):
        command = sub.add_parser(name)
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--n", type=int, default=4000)
    for name in ("promote", "rollback"):
        sub.add_parser(name).add_argument("version")
    monitor = sub.add_parser("monitor")
    monitor.add_argument("--shifted", action="store_true")
    sub.add_parser("status")
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    batch = sub.add_parser("batch")
    batch.add_argument("input", type=Path)
    batch.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    store = Store(args.root)
    try:
        if args.command in ("train", "demo"):
            result = train(store, args.seed, args.n)
            if args.command == "demo" and result["report"]["passed"]:
                store.promote(result["version"])
                _, bundle = store.load()
                stable, _ = generate(1000, 99)
                shifted, _ = generate(1000, 99, shifted=True)
                result["monitoring"] = {"reference_like": drift(bundle, stable),
                                        "shifted": drift(bundle, shifted)}
            print(json.dumps(result, indent=2))
            return 0 if result["report"]["passed"] else 2
        if args.command in ("promote", "rollback"):
            store.promote(args.version, rollback=args.command == "rollback")
            print(json.dumps({"active": args.version, "action": args.command}))
        elif args.command == "status":
            print(json.dumps(store.status(), indent=2))
        elif args.command == "monitor":
            version, bundle = store.load()
            x, _ = generate(1000, 99, shifted=args.shifted)
            report = drift(bundle, x)
            store.audit("monitoring", version, report)
            print(json.dumps(report, indent=2))
        elif args.command == "batch":
            x = validate(json.loads(args.input.read_text(encoding="utf-8")))
            version, bundle = store.load()
            # Exclusive creation prevents accidental overwrite of source data.
            with args.output.open("x", encoding="utf-8") as f:
                json.dump({"version": version, "probabilities": predict(bundle, x).tolist()}, f)
            store.audit("batch", version, {"count": len(x)})
        elif args.command == "serve":
            from .api import create_app
            create_app(args.root).run(host=args.host, port=args.port, debug=False)
        return 0
    except (ValueError, LookupError, OSError, json.JSONDecodeError) as error:
        print(f"MedMLOps: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
