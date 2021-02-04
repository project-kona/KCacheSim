# Copyright © 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

#!/bin/bash

INTERNAL_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function cachegrind() {

    set -x

    OUTPUT_PREFIX=${1}
    CACHE_PARAMS=${2}
    COMMAND=${3}

    mkdir -p $(dirname ${OUTPUT_PREFIX})

    ${INTERNAL_SCRIPT_DIR}/../valgrind/build/bin/valgrind \
        --tool=cachegrind ${CACHE_PARAMS} \
        --cachegrind-out-file=${OUTPUT_PREFIX}.cachegrind.detail \
        --log-file=${OUTPUT_PREFIX}.cachegrind.out -v \
        --trace-children=yes \
        ${COMMAND} &> ${OUTPUT_PREFIX}.cmd.out

}

# echo $# arguments 
if [ $# -ne 5 ]; then
    echo "Illegal number of parameters"
    exit
fi

# Arguments
SIMULATOR=${1}
UNIQUE_ID=${2}
CACHE_PARAMS=${3}
OUTPUT_PREFIX=${4}
METHOD=${5}
