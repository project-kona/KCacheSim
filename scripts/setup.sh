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

sudo python3 -m pip install chart_studio

# Setup all applications
${SCRIPT_DIR}/../apps/redis/setup.sh
${SCRIPT_DIR}/../apps/metis/setup.sh
${SCRIPT_DIR}/../apps/turi/setup.sh

# Set up ploty
sudo apt-get install -y libgtk2.0-0 libgconf-2-4 xvfb libxtst6 libxss1 libnss3 libasound2
curl -sL https://deb.nodesource.com/setup_12.x | sudo /bin/bash - && \
sudo apt-get install -y nodejs && \
sudo npm install -g electron@1.8.4 --unsafe-perm=true && \
sudo npm install -g orca && \
sudo sh -c "echo 'alias orca=\"xvfb-run -a /usr/bin/orca\"' >> /etc/bash.bashrc" && \
sudo python3 -m pip install psutil

# Making sure orca is setup
orca --help

sudo python3 -m pip install chart_studio pandas matplotlib scipy
