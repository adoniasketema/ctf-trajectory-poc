#!/usr/bin/env python3
"""
pick_nyu_tasks.py -- source 5 NYU CTF Bench (test) challenges into tasks/.

Reproducible: a fixed random seed picks the same 5 every run. We draw only from
FILE-ONLY challenges (no docker-compose in the folder), because the current
harness can't stand up the live-service challenges. Same 5 serve every model.

Usage (run from the project root, with -I since the repo is untrusted data):
    python3 -I scripts/pick_nyu_tasks.py <path-to-NYU_CTF_Bench/repo> tasks

It only READS and COPIES challenge files; it never executes them.
"""
import json, os, random, re, shutil, sys

SEED = 42
N = 5


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "chal"


def main():
    repo, out_tasks = sys.argv[1], sys.argv[2]
    test = os.path.join(repo, "test")

    # find every file-only challenge: has challenge.json + flag + files, no docker-compose
    candidates = []
    for root, _dirs, names in os.walk(test):
        if "challenge.json" not in names:
            continue
        if any(n in names for n in ("docker-compose.yml", "docker-compose.yaml")):
            continue  # needs a live service -> skip
        try:
            meta = json.load(open(os.path.join(root, "challenge.json")))
        except Exception:
            continue
        if not meta.get("flag") or not meta.get("files"):
            continue
        # every listed file must actually be present and be a regular file
        files = meta["files"]
        if not all(os.path.isfile(os.path.join(root, f)) for f in files):
            continue
        candidates.append((root, meta))

    print(f"file-only candidates: {len(candidates)}")
    random.seed(SEED)
    chosen = random.sample(candidates, N)

    chosen_slugs = []
    for root, meta in chosen:
        name = meta["name"]
        s = slug(name)
        # disambiguate with category if the slug collides
        if s in chosen_slugs:
            s = f"{slug(meta.get('category','x'))}-{s}"
        chosen_slugs.append(s)
        tdir = os.path.join(out_tasks, s)
        os.makedirs(os.path.join(tdir, "files"), exist_ok=True)
        for f in meta["files"]:
            shutil.copy(os.path.join(root, f), os.path.join(tdir, "files", os.path.basename(f)))
        prompt = (meta.get("description", "").strip() +
                  f"\n\nCategory: {meta.get('category','?')}. "
                  f"Files available in /work: {', '.join(os.path.basename(f) for f in meta['files'])}.")
        open(os.path.join(tdir, "prompt.txt"), "w").write(prompt.strip())
        open(os.path.join(tdir, "flag.txt"), "w").write(meta["flag"])
        print(f"  {s:28} [{meta.get('category','?'):8}] {name}")

    print("\nconfig tasks list:")
    print(json.dumps(chosen_slugs))


if __name__ == "__main__":
    main()
