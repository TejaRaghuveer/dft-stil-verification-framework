#!/usr/bin/env python3
"""Waveform analysis report generator from manifest/wave metadata."""

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-waveform", required=True)
    ap.add_argument("-output", required=True)
    ap.add_argument("-highlight_failure", action="store_true")
    args = ap.parse_args()

    wave = args.waveform
    mf = Path(wave).with_suffix(".waveform_manifest.json")
    manifest = {}
    if mf.exists():
        manifest = json.loads(mf.read_text(encoding="utf-8"))
    body = ["<h1>Waveform Analysis</h1>", f"<p>Waveform: {wave}</p>"]
    if manifest:
        body.append(f"<pre>{json.dumps(manifest, indent=2)}</pre>")
    if args.highlight_failure:
        body.append("<p>Failure highlight enabled.</p>")
    Path(args.output).write_text("<html><body>%s</body></html>" % "\n".join(body), encoding="utf-8")


if __name__ == "__main__":
    main()
