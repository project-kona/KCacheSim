#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${SCRIPT_DIR}/../../scripts/simulators.sh

PORT=$((30000 + ${UNIQUE_ID}))

ulimit -n 1048576

pushd ${SCRIPT_DIR}/redis

    ${SIMULATOR} ${OUTPUT_PREFIX} "${CACHE_PARAMS}" \
        "./src/redis-server ./redis.conf --port $PORT" &

popd


echo $(pgrep --parent ${!})


echo Waiting for Redis to start
sleep 5

function method_rand() {
    # final
    memtier_benchmark -p $PORT -t 10 -n 400000 --ratio 1:1 -c 20 -x 1 --key-pattern R:R --hide-histogram --distinct-client-seed -d 300 --pipeline=1000
}

method_$METHOD

sleep 10

set -x

time_pid=$(pgrep --parent ${!})
redis_pid=$(pgrep --parent ${time_pid})
third_pid=$(pgrep --parent ${redis_pid})
echo ${redis_pid}

cat /proc/${redis_pid}/status

# Kill redis from background
sudo kill -s SIGINT ${third_pid}
sudo kill -s SIGINT ${redis_pid}
sudo kill -s SIGINT ${time_pid}
