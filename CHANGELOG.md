# Changelog

What changed in each release of the anti-skill plugin. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-03

The first public release: two skills in one plugin, each measured against plain Claude Code.

### Added

- **evolve** keeps searching past the first correct answer, for anything with a score: it tries
  several approaches, improves the best one in rounds, and checks the winner on data it did not
  tune on. 23.4% faster code than plain Claude Code, and 9.1% faster than plain Claude Code told
  not to stop at the first answer that works.
- **profile-first** finds where a program's time really goes before anyone rewrites it: it
  confirms each hot spot by stubbing it out and timing the whole run. 81% smaller error on how
  much time the top hot spot takes; no better on harder tasks.

make-scorer and bench-fairly are in progress and not in this release. Each ships only after it
beats plain Claude Code on its own benchmark.

[1.0.0]: https://github.com/bombsdontbite/anti-skill/releases/tag/v1.0.0
