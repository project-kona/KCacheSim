#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

sudo apt-get update

# Build valgrind
pushd ${SCRIPT_DIR}/../valgrind
    ./autogen.sh &&
    ./configure --prefix=${SCRIPT_DIR}/../valgrind/build/
    make -j$(nproc)
    make install
popd

sudo python3 ${SCRIPT_DIR}/get-pip.py
sudo python ${SCRIPT_DIR}/get-pip.py

# Setup all applications
${SCRIPT_DIR}/../apps/redis/setup.py
${SCRIPT_DIR}/../apps/metis/setup.py
${SCRIPT_DIR}/../apps/turi/setup.py
