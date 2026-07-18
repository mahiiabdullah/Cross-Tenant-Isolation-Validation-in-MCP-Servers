# Release

Final artifact bundle for peer review (zip / tarball
instructions, checksums, signed tags).

## Contents

- `TOOL_CATALOGUE.md` — the reference MCP server's tool
  catalogue, with per-tool arguments and per-server
  exposure.
- `CHECKSUMS.txt` — SHA-256 checksums of every artefact in
  `analysis/tables/` and `analysis/figures/`. The single
  observed difference between re-runs is the `started_at` /
  `ended_at` ISO timestamps in `meta.json`; the CSV contents
  are otherwise bit-identical.

## Building a release tarball

```bash
git tag -s v0.1.0 -m "Phase-12 review bundle"
git archive --format=tar.gz --prefix=mcp-iso-0.1.0/ v0.1.0 \
    > mcp-iso-0.1.0.tar.gz
```

## Verifying a release

```bash
git verify-tag v0.1.0
git archive --format=tar.gz v0.1.0 | tar -tzf - | sort > /tmp/files.txt
sha256sum -c artifact/release/CHECKSUMS.txt
```

## Signed-tag recipe

The maintainer's GPG key is provisioned locally (the
reviewer's key is not assumed). The signed-tag recipe is:

```bash
git config --global user.signingkey <KEY_ID>
git tag -s v0.1.0 -m "Phase-12 review bundle"
```

The `git verify-tag` step above checks the signature against
the local keyring.