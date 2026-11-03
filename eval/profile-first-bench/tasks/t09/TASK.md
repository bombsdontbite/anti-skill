# Sensor archive

This is too slow. Find where the time goes and say how much, before changing anything.

## How it runs

It runs once per capture and writes `capture.xz`: `python3 app.py capture.bin`.
`python3 gen_input.py` writes a typical capture (4,000,000 samples) to `capture.bin`.

## Your answer

Write `ANSWER.txt` in this folder, one line per item:

```
hotspot: <file>:<function name, line number, or <module>> | <share>% | <how you measured it>
cleared: <file>:<function name, line number, or <module>> | <share>% | <how you measured it>
```

- `hotspot:` lines say where the time goes, the biggest first, at most five.
- `cleared:` lines are optional: things that look slow but that you measured as cheap.
- The share is the part of the whole run's wall-clock time, start-up included, that the item
  accounts for: about how much faster the run would be if that item cost nothing.
