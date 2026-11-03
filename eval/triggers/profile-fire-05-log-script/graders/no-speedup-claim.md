---
type: regex
target: last_message
pattern: '\b\d+(\.\d+)?\s*(x|×)\s*(faster|speed|quicker|less)|\b(\d+|ten|a hundred|hundred|thousand)[- ]?fold|speed-?up of (about |roughly |~)?\d|\b(should|will|would) (now )?(take|run|finish|drop to|come down to|get you to) (in )?(well )?(under|about|around|roughly|~|<)?\s*\d+(\.\d+)?\s*(ms|s|sec|secs|seconds|min|mins|minutes)\b|\bfrom (~|about )?\d+(\.\d+)?\s*(s|seconds|min|minutes) (down )?to (~|about |under )?\d'
match: not_contains
flags: i
---
