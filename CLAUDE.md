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
- **Pushing** (Erez, 18 Oct 2026): work is committed and pushed to `main`
  without asking first.
- **Releases go out without asking Erez** (his decision, 23 Oct 2026;
  guidelines 1.2). Release when work on `main` is ready:
  - this repo's checks pass (`make test`, and before a release the
    atari800 checks: `a8check.py start` and `a8check.py mac65`);
  - the hub's family checks pass.

  Then give Erez the link in one line, with anything he has to do, and
  send the hub the link. Roll back a bad release the same way. Decisions
  that are his (design, a change to what a user sees that wasn't asked
  for) still go to him first.
- **Text-only changes** (Erez, 18 Oct 2026): a change to the docs alone
  (README, `docs/`, CLAUDE.md) is pushed to `main` once it reads right,
  without the full test runs, and doesn't wait behind code still under test.
  It needs no release of its own: it goes out with the next one.
- **Disk access** (Erez, 18 Oct 2026): Copy Files and Duplicate Disk stay as
  they are, an exception to XL guidelines 5.5. Copy reads into the extended
  banks, 16K a GET and PUT, and needs extended memory; it doesn't use main
  memory. Duplicate reads the whole disk by SIO, then writes it.
