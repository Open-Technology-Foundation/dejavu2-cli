#!/bin/bash
set -euo pipefail

curl https://models.dev/api.json |jq . >models.dev.json

#fin
