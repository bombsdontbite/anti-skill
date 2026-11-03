#!/usr/bin/env bash
# gitleaks at one pinned release, its SHA-256 checked before it runs, over the whole history.
# gitleaks-action is not used: it needs a licence in an organization.
set -euo pipefail

# A new version means both lines: the SHA-256 is from the release's gitleaks_<v>_checksums.txt.
VERSION="8.30.1"
SHA256_LINUX_X64="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"

dir="${RUNNER_TEMP:-/tmp}/gitleaks-${VERSION}"
mkdir -p "$dir"
curl -fsSL --retry 3 -o "$dir/g.tar.gz" \
  "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_linux_x64.tar.gz"
sum="$(sha256sum "$dir/g.tar.gz" | cut -d' ' -f1)"
if [ "$sum" != "$SHA256_LINUX_X64" ]; then
  echo "::error::gitleaks ${VERSION}: SHA-256 is ${sum}, not the pinned one; nothing was run" >&2
  exit 1
fi
tar -xzf "$dir/g.tar.gz" -C "$dir" gitleaks
"$dir/gitleaks" detect --source . --redact --verbose --no-banner --exit-code 2
