#!/bin/bash
set -euo pipefail
cur_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <mode>" >&2
    exit 1
fi
export CONDA_VOLUME="${CONDA_VOLUME:-/home/heenj/anaconda3}"
source "$CONDA_VOLUME/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV:-jupyter}"
set -a
source "$cur_dir/conf/credentials"
set +a
exec python3 "$cur_dir/main.py" "$1"
