# Repository workflow

## Updates

- Run `./update.sh` from the repository root to update dotfiles. Do not replace it with ad hoc pulls or `git submodule update --remote`.
- The script updates the parent repository, then switches managed submodules to `main` and pulls them in parent-first order. It skips dependencies under `test` and `tests`.
- Resolve reported update failures before publishing. Preserve local changes; do not reset, clean, or force-push to bypass conflicts.

## Commits and pushes

- Inspect changes and unpublished commits in the parent repository and all managed submodules, including nested ones. Keep ignored machine-local files and secrets out of commits.
- Publish every managed submodule to its own `origin/main` before publishing the parent. Work from the deepest nested submodule outward; do not push third-party dependencies under `test` or `tests`.
- In each managed submodule, use `main`, commit its intended changes and any updated child-submodule pointers, then run `git push origin main`. Push existing unpublished commits even when its working tree is clean. Never create empty commits for unchanged modules.
- Only after all submodule pushes succeed, stage their updated pointers and intended root-file changes in the parent repository, commit them on `main`, and run `git push origin main` from the repository root.
- If any push fails, stop before publishing repositories that depend on it. Do not force-push. Report the failing repository and error.
- Report the published commits and verification performed. A parent commit must never reference a submodule commit that has not been published.
