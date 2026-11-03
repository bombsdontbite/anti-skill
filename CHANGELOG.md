# Changelog

What changed in each release of the anti-skill plugin. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-11-03

### Added

- A README inside the plugin folder (`plugins/anti-skill/README.md`): what each skill is for, how
  to call it, what it needs, and where the measured results are. Plugin directories show this
  file, and the Claude plugin directory requires one.
- A link from the README to the article about how the skills were built and measured.
- A chart in RESULTS.md of evolve's gain over plain Claude Code on both tasks, drawn from the
  committed results; CI fails if it drifts from them. Drawing it caught plain Claude Code's mean
  on the speed task printed as 71.4x instead of 71.3x; the percentages did not change.

### Changed

- The trigger counts are measured again with Claude Code 2.1.317: evolve loads on its own on 74%
  of its requests on Sonnet 5.5, not 7%. The 7% came from an older Claude Code that did not fully
  recognise Sonnet 5.5, and the advice to call evolve by name on Sonnet is withdrawn. Opus and Fable
  are within a few points of before; raw output for all six counts is committed.
- The README and RESULTS.md now say that on harder profiling tasks profile-first did worse than
  plain Claude Code on four of six measures, as the results table shows, instead of "did no
  better".
- The raw output of one trigger run no longer names the local time zone in its plan-limit
  messages. No count changed.

### Fixed

- profile-first's comparison script no longer runs the changed copy inside your project: both
  copies must be given, outside the project and apart from each other. It now checks the output on
  every timed run, not only the first, and exits with status 3 when the output differs.

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
