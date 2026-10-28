#!/usr/bin/env python3
"""
build_graph.py  --  layered, transparent trajectory-graph builder (POC)

Two layers over the SAME raw traces, matching the two altitudes in the goal:

  LAYER A  "summarize the sequence an agent did"   (per run, faithful)
     Every turn is a node. Only EXACT consecutive repeats are collapsed into one
     node with a xN count (so loops are visible without hiding what happened).
     This is a readable map of one agent's run -- not aggregated.

  LAYER B  "which paths are most traversed / lead to bad nodes"  (across runs)
     The coarse node buckets, aggregated. We report:
       - node visits and edge weights            (exact counts)
       - MOTIFS: frequent 2- and 3-step sub-paths (exact counts across all runs)
       - per-node BADNESS RATE: of runs passing through a node, the share that
         end in FAILED and the share that touch OUT_OF_SCOPE.
     We deliberately do NOT report a single "most-traversed full path": whole-run
     sequences almost never repeat, so that number is degenerate. Motifs are the
     honest version of "most traversed", and badness rate the honest version of
     "leads to bad nodes".

Dependencies: Python 3 standard library only. Deterministic. No network.
Every number can be re-derived by hand from the input JSONL.

Run:
    python3 build_graph.py example_traces.jsonl                 # both layers, all runs
    python3 build_graph.py example_traces.jsonl --model haiku   # filter one model
    python3 build_graph.py example_traces.jsonl --layer B       # just the aggregate
    python3 build_graph.py example_traces.jsonl --dot graph.dot # emit Graphviz (layer B)
"""

import sys, json, argparse
from collections import Counter, defaultdict

BAD_NODES = {"OUT_OF_SCOPE", "FAILED"}      # the nodes we call "bad"
TERMINALS = {"SOLVED", "FAILED"}            # run end states (excluded from badness table)


def load(path):
    """Read JSONL -> list of trajectories. A bad line fails loudly, not silently."""
    out = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"line {i}: bad JSON: {e}")
    return out


def node_sequence(tr):
    """Full node list for one run, synthetic START first -- the unit layer B counts."""
    return ["START"] + [s["node"] for s in tr["steps"]]


def ngrams(seq, n):
    return list(zip(*[seq[i:] for i in range(n)]))


# ---------------------------------------------------------------- LAYER A ----
def layer_a(traj):
    print("\n################  LAYER A -- per-run faithful summaries  ################")
    print("(every turn kept; only exact consecutive repeats collapsed as xN)\n")
    for tr in traj:
        # collapse consecutive identical (bucket, command-signature) turns
        chain = []
        for s in tr["steps"]:
            sig = (s["node"], (s.get("cmd") or "")[:38])
            if chain and chain[-1][0] == sig:
                chain[-1][1] += 1
            else:
                chain.append([sig, 1])
        parts = []
        for (node, cmd), c in chain:
            label = node if not cmd else f"{node}({cmd.strip()})"
            parts.append(label + (f" x{c}" if c > 1 else ""))
        head = f"{tr.get('model','?'):<7} {tr.get('task','?'):<16} {tr.get('outcome','?')}"
        print(head)
        print("   START -> " + "\n           -> ".join(parts) + "\n")


# ---------------------------------------------------------------- LAYER B ----
def layer_b(traj, dot_path=None):
    print("\n################  LAYER B -- aggregate behavior graph  ################\n")

    node_visits = Counter()
    edge_weight = Counter()
    motif2 = Counter()
    motif3 = Counter()
    for tr in traj:
        seq = node_sequence(tr)
        node_visits.update(seq)
        edge_weight.update(ngrams(seq, 2))
        motif2.update(ngrams(seq, 2))
        motif3.update(ngrams(seq, 3))

    solved = sum(1 for t in traj if t.get("outcome") == "solved")
    print(f"trajectories: {len(traj)}   solved: {solved}   failed: {len(traj)-solved}\n")

    print("node visits (exact):")
    for n, c in node_visits.most_common():
        print(f"  {n:<14} {c}{'   <-- BAD' if n in BAD_NODES else ''}")

    print("\nedge weights (exact, a -> b : count):")
    for (a, b), c in edge_weight.most_common():
        print(f"  {a:<14} -> {b:<14} {c}{'   <-- into BAD' if b in BAD_NODES else ''}")

    # MOTIFS = honest "most traversed paths": recurring sub-paths, counted
    # wherever they occur regardless of the surrounding run.
    print("\nmost-traversed MOTIFS (3-step sub-paths, count across all runs):")
    for mot, c in motif3.most_common(8):
        flag = "   <-- reaches BAD" if mot[-1] in BAD_NODES else ""
        print(f"  [{c}x]  " + " -> ".join(mot) + flag)

    # BADNESS RATE = honest "leads to bad nodes": per node, the share of runs
    # through it that end FAILED / that touch OUT_OF_SCOPE.
    print("\nper-node BADNESS RATE (of runs passing through the node):")
    print(f"  {'node':<14} {'runs thru':>9} {'end FAILED':>12} {'touch OOS':>12}")
    for n in ["START", "INSPECT", "WORK", "OUT_OF_SCOPE", "SUBMIT"]:
        thru = [t for t in traj if n in node_sequence(t)]
        if not thru:
            continue
        fail = sum(1 for t in thru if node_sequence(t)[-1] == "FAILED")
        oos = sum(1 for t in thru if "OUT_OF_SCOPE" in node_sequence(t))
        print(f"  {n:<14} {len(thru):>9} "
              f"{fail/len(thru):>11.0%} {oos/len(thru):>11.0%}")

    if dot_path:
        write_dot(dot_path, node_visits, edge_weight)
        print(f"\nwrote DOT: {dot_path}   (render: dot -Tsvg {dot_path} -o graph.svg)")


def write_dot(path, node_visits, edge_weight):
    lines = ["digraph trajectories {", "  rankdir=LR;",
             '  node [shape=ellipse, fontname="monospace"];']
    for n, c in node_visits.items():
        color = "red" if n in BAD_NODES else ("green" if n == "SOLVED" else "black")
        lines.append(f'  "{n}" [label="{n}\\n{c}", color={color}];')
    for (a, b), c in edge_weight.items():
        lines.append(f'  "{a}" -> "{b}" [label="{c}", penwidth={1 + c}];')
    lines.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("traces")
    ap.add_argument("--model", help="only count runs from this model")
    ap.add_argument("--layer", choices=["A", "B", "AB"], default="AB")
    ap.add_argument("--dot", help="write a Graphviz DOT of layer B to this path")
    args = ap.parse_args()

    traj = load(args.traces)
    if args.model:
        traj = [t for t in traj if t.get("model") == args.model]
    if not traj:
        sys.exit("no trajectories after filtering")

    if "A" in args.layer:
        layer_a(traj)
    if "B" in args.layer:
        layer_b(traj, args.dot)
    print()


if __name__ == "__main__":
    main()
