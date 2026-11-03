"""Score every condition of a run on a held-out set nobody has seen.

usage: final_scores.py <run> [task ...]
- bon: every cand_XX.py is scored on train; the best is the pick; cand_01 is the one-shot answer.
- iter, evolve: final.py is the pick.
Held-out = --split test with LOOP_BENCH_TEST_SEED set to a value no agent saw; speedup is scored
3 times and the median kept. Writes runs/<run>/final_scores.json.
"""
import json, os, statistics, subprocess, sys

B = os.path.dirname(os.path.abspath(__file__))
run = sys.argv[1]
tasks = sys.argv[2:] or ['binpack', 'tsp', 'cache', 'speedup', 'schedule', 'regex', 'knapsack', 'coloring', 'dedup']
SEED = 'anti-skill-heldout-' + run

def score(task, path, split):
    env = dict(os.environ)
    if split == 'test':
        env['LOOP_BENCH_TEST_SEED'] = SEED
    reps = 3 if task == 'speedup' else 1
    vals = []
    for _ in range(reps):
        out = subprocess.run(['nice', '-n', '10', 'python3', 'score.py', path, '--split', split],
                             cwd=f'{B}/{task}', env=env, capture_output=True, text=True).stdout
        r = json.loads(out.strip().splitlines()[-1])
        vals.append(r['score'] if r.get('valid') else None)
    ok = [v for v in vals if v is not None]
    return statistics.median(ok) if len(ok) == reps else None

res_path = f'{B}/runs/{run}/final_scores.json'
res = json.load(open(res_path)) if os.path.exists(res_path) else {}
for t in tasks:
    r = {'baseline_test': score(t, f'{B}/{t}/candidate_baseline.py', 'test')}
    bon = f'{B}/runs/{run}/bon/{t}'
    if os.path.isdir(bon):
        cands = sorted(f for f in os.listdir(bon) if f.startswith('cand_') and f.endswith('.py'))
        train = {c: score(t, f'{bon}/{c}', 'train') for c in cands}
        valid = {c: v for c, v in train.items() if v is not None}
        best = max(valid, key=valid.get) if valid else None
        r['bon_n'] = len(cands); r['bon_valid'] = len(valid)
        r['oneshot_test'] = score(t, f'{bon}/cand_01.py', 'test') if 'cand_01.py' in cands else None
        r['bon_pick'] = best; r['bon_train'] = valid.get(best)
        r['bon_test'] = score(t, f'{bon}/{best}', 'test') if best else None
    for cond in ('iter', 'evolve'):
        f = f'{B}/runs/{run}/{cond}/{t}/final.py'
        if os.path.exists(f):
            r[f'{cond}_train'] = score(t, f, 'train'); r[f'{cond}_test'] = score(t, f, 'test')
            log = f'{B}/runs/{run}/{cond}/{t}/calls.log'
            r[f'{cond}_calls'] = sum(1 for _ in open(log)) if os.path.exists(log) else 0
    res[t] = r
    print(t, json.dumps(r))
json.dump(res, open(res_path, 'w'), indent=1)
