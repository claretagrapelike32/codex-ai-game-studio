# Release artifacts

Release archives are generated, not edited by hand:

```text
python tools/build_release.py --version 1.0.0 --output dist
```

The builder creates one complete marketplace ZIP, seven standalone plugin ZIPs,
an SPDX 2.3 JSON SBOM, a machine-readable release manifest, and `SHA256SUMS`.
Every ZIP uses sorted paths, fixed file metadata, and the DOS epoch timestamp so
identical source trees produce identical bytes across Windows, macOS, and Linux.

GitHub's release workflow validates the repository, rebuilds the artifacts, and
adds a GitHub build-provenance attestation. A release must be triggered from an
existing `vMAJOR.MINOR.PATCH` tag; the workflow does not create or move tags.
