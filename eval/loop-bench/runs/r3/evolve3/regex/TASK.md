# A regex for our date strings

One of our input fields only accepts strings in a certain format. I don't have a written spec,
only examples: `train_examples.json` lists strings that should be accepted (`positive`) and
strings that should be rejected (`negative`). The current check is `candidate_baseline.py`; I
want a Python regular expression that separates the two much better.

Write a Python file defining one string:

    PATTERN = r"..."

It is used with `re.fullmatch(PATTERN, s)` (the whole string must match). A match means
"accept".

Better means more accurate and still readable: the score is the share of strings classified
correctly minus 0.001 per character of `PATTERN`. The final score is taken on a fresh, larger
batch of strings of the same kind, not on the examples you have, so a pattern that just lists
the examples will do badly.

Constraints: at most 2000 characters; matching the whole batch must finish within 10 seconds
(watch out for catastrophic backtracking). Python's standard `re` module only. Do not read
files at run time — `PATTERN` must be a literal or built from literals; no file access,
eval/exec, getattr or dunder attributes — the scorer rejects the file outright.

Score a candidate with `./score my_candidate.py`.
