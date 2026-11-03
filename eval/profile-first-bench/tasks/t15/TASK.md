# Scan archiver

This is too slow. Find where the time goes and say how much, before changing anything.

## How it runs

It runs once per scanned page and writes `page.bz2`: `python3 app.py page.raw`.
`python3 gen_input.py` writes a typical page (2976 x 4209 pixels) to `page.raw`.

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
