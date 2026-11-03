# anti-skill

Two Claude Code skills for the moment an agent says "done" too early. Both run longer than plain
Claude Code on purpose: the extra time goes into measuring.

- **evolve**, for anything with a score (speed, a benchmark, a metric backed by tests). It tries
  several different approaches, improves the best ones in rounds while time and tries remain, and
  checks the winner on data it did not tune on. Say "a quick look" for about 5 minutes or "take
  your time" for no time limit; the default is about 15 minutes.
- **profile-first**, for a program that is slow when nobody knows why. It profiles an input of real
  size, confirms each hot spot by stubbing it out and timing the whole run, and clears what only
  looks slow. Its scripts need Python 3.9 or later, on macOS or Linux.

Just ask in your own words, for example "make this function faster" or "why is this script so
slow?", and the right skill loads on its own. If it does not, call it by name:
`/anti-skill:evolve` or `/anti-skill:profile-first`.

Neither skill adds a network call or sends data anywhere: they run your own code and tests on your
machine.

Results against plain Claude Code, including the ties and the losses, and how each number was
measured: https://github.com/bombsdontbite/anti-skill
