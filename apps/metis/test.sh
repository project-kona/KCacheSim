#!/bin/bash


SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${SCRIPT_DIR}/../../scripts/simulators.sh

pushd ${SCRIPT_DIR}/Metis

function method_linreg() {
    ${SIMULATOR} ${OUTPUT_PREFIX} "${CACHE_PARAMS}" \
        "./obj/linear_regression ./data/lr_40GB.txt -p 8"
}

method_$METHOD

popd