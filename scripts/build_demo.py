#!/usr/bin/env python3
"""Build the public demo exclusively from newly generated synthetic inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signal_origin.experiment import analyze
from signal_origin.synthetic_v4 import make_inputs


def payload():
    inputs, weather, monthly = make_inputs()
    result = analyze(inputs, weather, monthly, allow_synthetic=True)
    data = {"meta": {**result["meta"], "generator": "signal_origin.synthetic_v4; seeds 42 and 590",
                     "experiment": "SYNTHETIC_SOFTWARE_TEST_ONLY"},
            "metrics": json.loads(result["metrics"].to_json(orient="records", date_format="iso", double_precision=15)),
            "annual": json.loads(result["annual"].to_json(orient="records", date_format="iso", double_precision=15)),
            "rows": json.loads(result["predictions"].to_json(orient="records", date_format="iso", double_precision=15)),
            "prices": [[d.strftime("%Y-%m-%d"), float(v)] for d, v in
                       zip(inputs.frame.price_date, inputs.frame.close_us_cents_per_lb)]}
    for row in data["rows"]:
        for key, value in row.items():
            if isinstance(value, str) and "T00:00:00" in value:
                row[key] = value[:10]
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    data["meta"]["payload_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Rebuild in memory and require byte-identical checked-in HTML.")
    args = parser.parse_args()
    data = payload()
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    template = (ROOT / "demo/template.html").read_text(encoding="utf-8")
    if template.count("__PAYLOAD__") != 1:
        raise ValueError("The demo template must contain exactly one payload placeholder.")
    rendered = template.replace("__PAYLOAD__", encoded)
    target = ROOT / "demo/index.html"
    if args.check:
        if target.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Demo differs from the reproducible synthetic build.")
        print("Synthetic demo matches its generator and template.")
    else:
        target.write_text(rendered, encoding="utf-8")
        print(f"Built demo/index.html: {len(data['rows'])} synthetic forecast rows; no third-party records.")


if __name__ == "__main__":
    main()
