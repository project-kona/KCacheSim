#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${SCRIPT_DIR}/../../scripts/simulators.sh

SRC_DIR=${SCRIPT_DIR}/

# Run app_graph_analytics.py -g [wiki/twitter] -a [pagerank/connectedcomp/labelprop/graphcol]

function method_graphcol() {
    ${SIMULATOR} ${OUTPUT_PREFIX} "${CACHE_PARAMS}" \
        "python ${SRC_DIR}/app_graph_analytics.py -g twitter -a graphcol"
}

method_$METHOD
