#!/bin/bash
set -e

HUGO_VERSION="0.157.0"

echo "=== Installing Hugo v${HUGO_VERSION} ==="
curl -L -o hugo.tar.gz \
  "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz"
tar xzf hugo.tar.gz
rm hugo.tar.gz
echo "Hugo ready: $(./hugo version)"

echo "=== Building Hugo site ==="
./hugo --minify --buildFuture

echo "=== Installing Node dependencies ==="
npm install

echo "=== Build complete ==="
