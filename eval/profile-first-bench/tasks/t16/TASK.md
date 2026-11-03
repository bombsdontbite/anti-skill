# Merchant settlement

This is too slow. Find where the time goes and say how much, before changing anything.

## How it runs

It runs once per day of card payments: `python3 app.py payments.csv`. A production day is
about 60,000 payments from about 20 merchants. `python3 gen_input.py` writes the file the tests
use: 60,000 payments spread over 15,000 merchants; `--merchants N` spreads them over N instead.

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
