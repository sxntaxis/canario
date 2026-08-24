# Pre-release rename: ActaKit -> Canario

Canario is the current product/repository/package name. The rename is architectural as well
as cosmetic: “ActaKit” over-signaled the first mature source family and made minutes-shaped
assumptions easier to introduce accidentally.

## Renamed in the current tree

- Python package: `actakit` -> `canario` (no compatibility alias; pre-release has no API
  compatibility obligation);
- active README/AGENTS/docs product language;
- current tests/proof-script imports and temporary state names;
- intended canonical GitHub repository path: `sxntaxis/canario`.

## Deliberately not rewritten

- Git history;
- old Notebook prose/certification evidence that truthfully described ActaKit-era paths;
- stable accepted contract/fixture identifiers such as `ACTAKIT-ARCH-001` and `AKF-*`;
- frozen migration `0001` bytes solely for branding. The SQL artifact must not lose its
  certified hash just to update a comment.

These are provenance, not current product-scope signals.

## Remote cutover

A local bundle cannot rename the canonical GitHub repository. After this checkpoint is
accepted against the canonical repo, rename the remote repository to `sxntaxis/canario`
and update the canonical remote before pushing this branch. Do not create an `actakit`
Python compatibility package unless a later public compatibility boundary explicitly
requires one.
