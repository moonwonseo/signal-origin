"""Offline command-line entry points; only the explicit demo generates fake data."""
import argparse
from pathlib import Path
import sys

from .io import load_inputs, load_json, write_json
from .runner import fresh_directory, plan_to_folder, run_experiment, validate_to_folder
from .spec import RunConfig, SignalOriginError
from .synthetic import write_synthetic_inputs


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Signal-Origin B0/B1: exact +10% at 63 exchange sessions; no weather or live trading.")
    subs = p.add_subparsers(dest="command", required=True)
    for command in ("validate", "plan", "run"):
        sub = subs.add_parser(command)
        sub.add_argument("--prices", type=Path, required=True)
        sub.add_argument("--sessions", type=Path, required=True)
        sub.add_argument("--metadata", type=Path, required=True)
        sub.add_argument("--out", type=Path, required=True)
        if command in ("plan", "run"):
            sub.add_argument("--config", type=Path, required=True)
            sub.add_argument("--allow-synthetic", action="store_true")
    demo = subs.add_parser("demo", help="Artificial mechanics check only; no historical data are used.")
    demo.add_argument("--out", type=Path, required=True)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "demo":
            fresh_directory(args.out)
            paths = write_synthetic_inputs(args.out / "SYNTHETIC_INPUTS")
            inputs = load_inputs(**paths)
            config = RunConfig(test_start=inputs.frame["price_date"].iloc[1200].strftime("%Y-%m-%d"),
                               test_end=inputs.frame["price_date"].iloc[1650].strftime("%Y-%m-%d"))
            write_json(args.out / "SYNTHETIC_config.json", config.to_dict())
            result = run_experiment(inputs, config, args.out / "SYNTHETIC_RUN", allow_synthetic=True)
            print("SYNTHETIC SOFTWARE TEST ONLY — not a real coffee forecast or performance claim.")
        else:
            inputs = load_inputs(args.prices, args.sessions, args.metadata)
            if args.command == "validate":
                result = validate_to_folder(inputs, args.out)
                print("Input audit written. No model was fitted.")
                if result["model_readiness_blockers"]:
                    print("MODELING BLOCKED: " + " ".join(result["model_readiness_blockers"]))
                    print(f"Output: {args.out.resolve()}")
                    return 2
            else:
                config = RunConfig.from_dict(load_json(args.config))
                if args.command == "plan":
                    result = plan_to_folder(inputs, config, args.out, args.allow_synthetic)
                    print("Split audit written. No model was fitted.")
                else:
                    result = run_experiment(inputs, config, args.out, args.allow_synthetic)
                    print(f"Completed: {result['evidence_status']}. No claim of forecasting skill.")
        print(f"Output: {args.out.resolve()}")
        return 0
    except (SignalOriginError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
