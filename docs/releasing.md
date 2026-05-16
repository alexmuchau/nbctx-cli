# Releasing nbctx

This project is set up for PyPI Trusted Publishing from GitHub Actions.

## One-time PyPI setup

Create the PyPI project/trusted publisher for `nbctx` with these values:

- Project name: `nbctx`
- Owner: `alexmuchau`
- Repository: `nbctx-cli`
- Workflow: `release.yml`
- Environment: `pypi`

In GitHub, create an environment named `pypi`. For safer releases, require manual approval on that environment.

## Release flow

1. Update the version in `pyproject.toml` and `src/nbctx/__init__.py`.
2. Update `CHANGELOG.md`.
3. Run local verification:

   ```bash
   uv sync
   uv run pytest -q
   uv build
   ```

4. Commit and push.
5. Create and push a semver tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

GitHub Actions will build and publish to PyPI through OIDC. No PyPI API token is needed in repository secrets.

## Homebrew tap

After the PyPI release exists, update the Homebrew formula with the release tarball URL and SHA256.

Recommended tap repository:

```text
alexmuchau/homebrew-tap
```

Users will install with:

```bash
brew tap alexmuchau/tap
brew install nbctx
```

Suggested first formula workflow:

```bash
git clone https://github.com/alexmuchau/homebrew-tap.git
cp packaging/homebrew/nbctx.rb.template ../homebrew-tap/Formula/nbctx.rb
cd ../homebrew-tap
brew update-python-resources Formula/nbctx.rb
brew audit --strict --online Formula/nbctx.rb
brew test nbctx
git add Formula/nbctx.rb
git commit -m "Add nbctx formula"
git push origin main
```

`brew update-python-resources` fills in the Python dependency `resource` blocks once the package is available from PyPI.
