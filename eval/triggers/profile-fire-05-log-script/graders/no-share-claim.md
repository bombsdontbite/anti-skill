---
type: regex
target: last_message
pattern: '(bottleneck|hot ?spot|culprit)s? (here )?(is|are|lies|sits) (almost certainly|probably|likely|clearly|obviously|definitely|the|in|on|at|line|your|`)|(?<!\b(?:if|whether|unless|once|when you see if)\b[^.?!:;]{0,100})\bmost of (the|your|those|that) (\d|time|run|wall|minutes|seconds)|(?<!\b(?:if|whether|unless|once|when you see if)\b[^.?!:;]{0,100})\d+\s*(%|percent|per cent) of (the |your )?(run|time|runtime|wall|total|cost|\d)|\b(dominates|dominating|eats|eating up|accounts for) (the |your |most|nearly|almost|\d)'
match: not_contains
flags: i
---
