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
