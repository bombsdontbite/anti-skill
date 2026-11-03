---
name: profile-first
description: "Measures where a program's time really goes before anything is sped up. Profiles a production-sized input in fresh processes, splits out import time and I/O wait, and confirms each hot spot by stubbing it out and timing the whole run. Use when the user asks to make code faster, find why something is slow, or cut run time, latency or startup, and before an optimisation loop such as evolve picks its target. Profiles Python commands that run to completion; ablation times any command. macOS and Linux. Also use it when the code is pasted or cannot be run here: it then names no hot spot and says what to measure. Not for a change the user has already specified."
---

# profile-first

**First: can the program run here? If not (pasted code, or a file or input that is not here),
the reply names no hot spot, not even as a likely one, gives no share, claims no speed-up and
writes no faster version. It says the code was not run and gives the commands that measure it
(step 2).**

This skill gets each hot spot's share of the run right, to about a point, by timing it, and
clears what only looks slow by a number. The measuring steps are scripts.

**Change no code for speed until `profile/result.json` names a hot spot backed by the file
ablate.py printed as `written`, with verdict `drop`. If it says why none was confirmed, change
nothing for speed unless the user names the change.**
If the user names the exact change, make it, and say no measurement backs it.

[hotspots.py](scripts/hotspots.py) (Python 3.9+, stdlib) and [ablate.py](scripts/ablate.py) (any
command) are in this skill's folder, for macOS and Linux. Neither needs root; never reach for sudo.
Run one profile at a time, on a quiet machine. If the project has a `profile/` of its own, pass
another folder as `--out` and read `profile/` below as that folder.

**Every step runs the command many times** (a profile 6 times, an ablation 16). Before the first
run, read what it touches. If it changes a database or a network service, sends anything, or
consumes or moves its inputs, run it only against a local copy or a stub of that, or ask the user.

## 1. A realistic input

A toy fixture points at the wrong place: a hidden O(n²) vanishes at 50 rows, and startup owns a
run that is too short.
- Ask for the production size, or find it in the ticket, logs or docs. Build a generator to that
  size with a fixed seed, `profile/make_input.py`; large data stays out of git.
- Aim for a run of a few seconds, at most about 30 s; past that, take the largest size under it
  and check n against 4n (below). If only a toy exists and no size can be learned, say so in the
  report and mark the input `"realistic": false`.
- Unsure of the size? Profile at n and 4n (`--out profile/n`, then `--out profile/4n --compare
  profile/n/hotspots.json`). A share that grows with n is superlinear and will own the production
  run. Then profile the production size into `profile/` (the default).

## 2. Profile in fresh processes

    python3 <skill>/scripts/hotspots.py --input-desc "what, how big" -- .venv/bin/python app.py ARGS

- Run it from the project root, with the project's interpreter first after `--`. `-m package.cli`
  works too.
- Pass `--check PATH` for each file the program writes, `--input PATH` for each input the
  arguments do not name (named files and folders are hashed already), `--env NAME` for each
  variable it reads, `--stdin FILE` for piped input.

It prints wall, CPU, I/O wait and import time, a table of Python frames (`self` and `incl` from
a sampler, beside cProfile's share), and cProfile's self time, where C calls appear by name.
`self` charges time in libraries (logging, re, json, I/O) to the nearest project frame.
- **cProfile inflates**: tracing inflated this row. Take the sampler's share.
- **waits**: wall time far exceeds CPU time: I/O, sleep, a lock or a child process.
- Treat imports as one more row: if its share beats the top row, ablate it first and gate with
  `--focus imports`.

## 3. Ablate down the `self` column, top row first

A share is a lead; the claim is a timing.
1. Copy the project outside itself: one base copy, `${TMPDIR:-/tmp}/base`, shared by every row's
   base arm, and per row two more beside it, `record-<name>` and `ablate-<name>`. Leave `.git`,
   `.venv` and data the command only reads out of each copy and symlink them to the originals.
   Delete a row's copies after it.
2. In the ablate copy, stub the row so the program leaves the same output by a cheaper route:
   - return values: record them in the record copy by call order, and replay them;
   - text written: write the recorded bytes;
   - a side effect: the cheapest equivalent, such as one commit at the end;
   - a module: a fake module that replays its results (deferring the import only moves the cost);
   - a library cost charged to a frame (logging, re, json): switch that library call off, not the
     frame.

   Run the record copy with `PYTHONHASHSEED=0`; ablate.py sets it for both arms. Make the stub
   raise once first: if the variant still exits 0, the copy imports the original (an editable
   install, a `src/` layout); run the variant as `env PYTHONPATH=<copy>/src ...`.
3. Time both arms, `<name>` being the row's name exactly as the table prints it. If the program
   writes files, pass each with `--check PATH`.

       python3 <skill>/scripts/ablate.py --name <name> --base "CMD" --variant "CMD" \
         --base-cwd "${TMPDIR:-/tmp}/base" --variant-cwd "${TMPDIR:-/tmp}/ablate-<name>"

4. Verdict `drop` means the drop cleared the noise; that drop is the share you report. `rise`
   means the stubbed run was slower: the stub costs more than what it replaced.
5. `output differs`: time the base against a copy of itself. If that differs, output varies between
   runs (see below). If only a file's bytes differ while its content matches (a database, an
   archive), check a dump of it (see below). Otherwise the stub changed the output: fix it.
6. Go down the table. Stop at the first row whose drop is at least half its `incl` share, or
   after the rows that cover 80% of `self`. Every `drop` row on the way is a hot spot. If none,
   rerun the top row's ablation once with more `--repeats`; if still none, write `"hot_spots": []`
   and `"why_none": "no row cleared the noise (floor X%)"`.

## 4. Clear the decoys

List what looks slow on reading (the nested loop, the regex, the scary block) and give each its
measured share: its `incl` share, or an ablation's drop. A decoy is cleared by a number, not an
argument. When the obvious loop measures as the hot spot, say so.

## 5. Report before any edit

`profile/REPORT.md`: the input (what, size, realistic or toy); wall, CPU, wait and import time;
each hot spot with its ablation drop and range, its profile shares and how each was measured;
the decoys with their shares; what was not covered (threads other than main, native code,
subprocesses); the exact commands that rebuild the input and reproduce every number.
`profile/result.json`, one line:

    {"command": str, "input": {"desc": str, "realistic": bool, "make": str|null},
     "wall_s": n, "cpu_s": n, "wait_s": n, "import_s": n,
     "hot_spots": [{"name": str, "share": n, "interval": [lo, hi], "method": "ablation", "profile_share": n}],
     "why_none": null|str, "decoys": [{"name": str, "share": n, "method": "sampler"|"ablation"}], "gate": null}

List hot spots biggest drop first. Copy every value from a file the scripts wrote: `command` from
`command_line` in `profile/hotspots.json` (the interpreter included), `share` and `interval` from
the file ablate.py printed as `written`, `profile_share` from `profile/hotspots.json`.

If a hot spot was confirmed, end your reply with one line telling the user that evolve can speed
it up with a measured loop.

## 6. The stop gate

After a change, re-profile with the same command, input and flags:

    python3 <skill>/scripts/hotspots.py --out profile/after --compare profile/hotspots.json --focus "<name>" -- .venv/bin/python app.py ARGS

It exits non-zero unless the output is unchanged, the hot spot's share fell beyond sampling noise,
and the wall median fell by more than either version's run range. A hot spot the change removed
counts as share 0. Nobody calls a speed-up done before it passes; copy `gate` from
`profile/after/hotspots.json` into `result.json`. The size of the speed-up is a timing (ablate.py
with old against new), not a share.
- `output changed`: the change broke the output; fix it.
- `share not beyond noise`: the change hit the wrong place; back to step 3.
- `wall within range` alone: the share fell, but the run times overlap. Profile the old version
  again, then the new, both with `--repeat 7`.
- A reason that starts `unclear`: see the closing section.

## When the defaults do not fit

- **Runs under 0.5 s**: pass `--repeat 7` to hotspots.py and `--repeats 21` to ablate.py.
- **A run may hang**: pass both scripts a `--timeout` of about 5× the first measured run.
- **A server or worker that never exits**: write a driver that starts the app in-process, sends
  N requests and exits. Profile the driver.
- **Threads and pools**: the sampler sees only the main thread, and a main thread waiting on busy
  workers is not flagged `waits`. If a pool or join frame dominates, profile the worker's entry
  point directly. On Linux, `py-spy record --subprocesses` needs no root.
- **A program that uses SIGALRM or `signal.alarm`**: the sampler ticks on that timer. hotspots.py
  warns `sampler stopped early`, or the run fails; profile a driver that skips that code.
- **hotspots.py warns `the sampler run took … plain`**: its timer cut a wait in C code short (a
  sleep, poll or select that does not retry), so the sampler's shares describe a shorter run. Rank
  by cProfile's column and ablate; gate with ablate.py, old version as base, new as variant.
- **Output that varies between runs** (a timestamp, an unseeded random): fix it with a seed or a
  flag in every command. Both scripts compare output.
- **A file whose bytes depend on how it was written** (a SQLite database, an archive): write
  `profile/run.py` that runs the program in-process (`runpy.run_path`) and then writes the file's
  content to `profile/out.dump`. Profile and ablate `profile/run.py` with
  `--check profile/out.dump`.
- **An input over 256 MB**: hotspots.py hashes that much of each input path and compares the
  rest by size and mtime; the report and the gate say `input check partial`. `--hash-mb` raises it.
- **A pipe or a redirect in a command**: ablate.py runs no shell; wrap it in `sh -c '...'`.
- **A row with a large `incl` share comes out `within noise` or `rise`**: suspect the stub before
  the row.
- **The gate says `unclear`**: on a different command, interpreter, directory, input, environment
  or `--check` set, profile the old version again with the same flags, then the new. On output
  that varies, fix it as above. On a name not in the old profile, pass `--focus` the name exactly
  as the old table prints it.
- **Not Python**: profile with the language's own sampler (`node --cpu-prof`, `go test
  -cpuprofile` with pprof, `perf` on Linux, Instruments on macOS). Steps 3–5 are the same with
  ablate.py. The gate is ablate.py with the old version as base and the new as variant: verdict
  `drop`, output identical.
