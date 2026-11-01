# Notes for working on EDOS

- **The name** reads "AERA | Erez Yaary" wherever it is given: copyright
  lines (`Copyright (C) 2026 AERA | Erez Yaary`), the docs, and as the
  author of every commit:
  `git commit --author="AERA | Erez Yaary <yaary@me.com>"`, with Claude as
  the signing committer (AERA-Atari, `standards/GITHUB-IDENTITY.md`).
- **Only formal releases leave the build machine.** Erez gets vX.Y releases
  made by the Release workflow from `main`, nothing else: no test builds, no
  dev builds, no CI artifacts, no builds from a branch. Work lands on `main`;
  to try a fix on real hardware, release it. If a release doesn't work, roll
  back with a release: revert on `main`, release the next number, and say in
  the bad release's notes that it is withdrawn and which one to use.
- **The one automatic update** (Erez's choice, 15 Oct 2026): on each push to
  `main`, CI replaces the latest release's `EDOS.ATR` and `EDOSTEST.ATR` when
  the built `EDOS.COM` is byte for byte the release's, so the disk carries the
  current sources. A changed program waits for the next release.
- **Talking with Erez** (his rule, 18 Oct 2026): no progress or in-between
  messages. Write to him only when he has to decide something, with a short
  context. For analysis: the information, your assessment, and what he should
  do.

  **Who decides what** (Erez, 31 Oct 2026; the guidelines' "Who decides
  what"). Erez's part, put to him before the work as a decision with a
  short context:
  - new programs and ideas, their core capabilities, and how they work with
    the other programs;
  - the user experience: the look, the layout, the way through a task, the
    words, the icons, the defaults;
  - phases: work stays inside the phase he approved; at its end, one phase
    report (what it set out to do, what was done with the release links,
    what is left, the next phase as a proposal), and the next phase starts
    when he says so;
  - priorities and conflicts between programs or sessions (through the hub,
    with its options and recommendation).

  How it is made is the team's, without asking: code, structure, shared
  code, tests, measurements, fixes, docs and releases inside an approved
  phase.
- **Pushing** (Erez, 18 Oct 2026): work is committed and pushed to `main`
  without asking first.
- **Releases go out without asking Erez** (his decision, 23 Oct 2026;
  guidelines 1.2). Release when work on `main` is ready:
  - this repo's checks pass (`make test`, and before a release the
    atari800 checks: `a8check.py start` and `a8check.py mac65`);
  - the hub's family checks pass.

  Then give Erez the link in one line, with anything he has to do, and
  send the hub the link. Roll back a bad release the same way. Decisions
  that are his ("Who decides what", above) still go to him first.
- **Text-only changes** (Erez, 18 Oct 2026): a change to the docs alone
  (README, `docs/`, CLAUDE.md) is pushed to `main` once it reads right,
  without the full test runs, and doesn't wait behind code still under test.
  It needs no release of its own: it goes out with the next one.
- **Disk access** (Erez, 18 Oct 2026): Copy Files and Duplicate Disk stay as
  they are, an exception to XL guidelines 5.5. Copy reads into the extended
  banks, 16K a GET and PUT, and needs extended memory; it doesn't use main
  memory. Duplicate reads the whole disk by SIO, then writes it.

## Maintenance mode (Erez, 1 Nov 2026)

EDOS is in maintenance mode while EWeb, EPDF and EPlay go to 1.0 (AERA-Atari, ATARI-XL-GUIDELINES.md, section 10). Until Erez ends it:
- No new features, speed rounds, clean-ups, or catching up with new or changed guidelines.
- No sync of the shared code (`xl/`). Shared code moving is no reason to rebuild or release.
- A release only for:
  - a security or data-loss fault;
  - a crash or breakage Erez reports;
  - something outside that stops it working.

  Such a release takes only that fix (one change from AERA-Atari, not a sync), and its notes say why.
- Work on `main` that isn't released stays unreleased.
- Nothing runs in the background; the session waits for Erez or the hub.
- Only Erez's explicit word ends this mode, for instance that every program is to take the latest shared code and release. The hub passes it on quoting him.
