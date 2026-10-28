#!/usr/bin/env python3
"""
to_viz.py -- feed labeled traces into the interactive viz.

The HTML embeds its data as a `const TRAJ = [ ... ];` array. This script
replaces that array in place with whatever labeled traces you pass, so real
runs show up in the same page. (JSON is valid JS, so quoted keys are fine.)

    python3 to_viz.py                       # uses ../labeled_traces.jsonl
    python3 to_viz.py ../example_traces.jsonl   # or any labeled JSONL
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "trajectory_graph.html")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "labeled_traces.jsonl")
    traces = [json.loads(l) for l in open(src) if l.strip()]
    array = "const TRAJ = " + json.dumps(traces, ensure_ascii=False, indent=1) + ";"

    html = open(HTML).read()
    new_html, n = re.subn(r"const TRAJ = \[.*?\n\];", array, html, count=1, flags=re.S)
    if n != 1:
        sys.exit("could not find the `const TRAJ = [ ... ];` block to replace")
    open(HTML, "w").write(new_html)
    print(f"updated {HTML} with {len(traces)} trajectories from {os.path.basename(src)}")


if __name__ == "__main__":
    main()
