#!/usr/bin/env bash
set -euo pipefail
KEY="${1:-/c/DAO/.deploy-secrets/hetzner_963x_nopass}"
ssh -i "$KEY" -o BatchMode=yes root@46.62.163.209 'docker exec selfhost-api-1 printenv UAP_CRYPTO_RECEIVER_WALLET UAP_CRYPTO_MODE'
