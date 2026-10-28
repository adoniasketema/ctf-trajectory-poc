# CTF Agent Trajectory Graph

Turn what an AI agent does while solving a CTF challenge into a **graph**: each
node is a *kind* of thing the agent did, edges show how often it moved from one
to the next, and clicking a node reveals the actual runs — and their thinking —
that passed through it.

## See the graph

Open the self-contained page in a web browser:

```bash
open trajectory_graph.html
```

Use the dropdowns to filter by **model** or **CTF task**; click a node (try the
red `OUT_OF_SCOPE`) to see the runs through it and their thinking traces.

## The 7 nodes

| node | meaning |
|------|---------|
| `START` | entry point (one per run) |
| `INSPECT` | looking at the files to understand the task |
| `WORK` | actually solving — decoding, computing, building tools |
| `OUT_OF_SCOPE` | trying to break the rules: sandbox escape, network probing, reading the harness **(bad)** |
| `SUBMIT` | proposing a flag |
| `SOLVED` | got the right flag |
| `FAILED` | wrong answer, timeout, or gave up **(bad)** |

## The data

The graph shows **mock** trajectories — generated to look like real runs, so you
can see the shape without paying for API calls. Regenerate or tweak them:

```bash
python3 scripts/mock_traces.py   # edit the PROFILE knobs / SAMPLES inside
python3 harness/to_viz.py        # load them into trajectory_graph.html
```

See the exact node / edge / motif counts behind the graph:

```bash
python3 build_graph.py labeled_traces.jsonl
```

## What's in here

| path | what it is |
|------|------------|
| `trajectory_graph.html` | the interactive graph (open this) |
| `build_graph.py` | prints exact node / edge / motif counts + a Graphviz file |
| `scripts/mock_traces.py` | generates the mock trajectories |
| `harness/` | optional: runs real Claude models on CTF tasks to produce real traces |
| `tasks/` | the CTF challenges (5 from NYU CTF Bench + 2 simple seeds) |
| `trace_schema.md`, `labeler_spec.md` | how traces and node labels are structured |

## Running real models (optional)

The `harness/` folder can run Claude (haiku / sonnet / opus) on the tasks inside
a locked-down Docker container and produce real traces. It needs Docker and an
Anthropic API key (`.env`). The approach and caveats are documented in
`trace_schema.md` and `labeler_spec.md`.
