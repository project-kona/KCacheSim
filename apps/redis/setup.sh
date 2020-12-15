#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pushd ${SCRIPT_DIR}

# Redis
##########################
git clone https://github.com/antirez/redis
pushd redis 
    make distclean # important! 
    make -j$(nproc)

    # Use already-provided Redis file
    cp ../redis-memory.conf ./redis.conf
popd

sudo sh -c "echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf"
sudo sysctl vm.overcommit_memory=1

sudo sh -c "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
sudo sh -c "echo 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' >> /etc/rc.local"


# Memtier
##########################
sudo apt-get install -y libpcre3-dev  libevent-dev

git clone https://github.com/RedisLabs/memtier_benchmark
pushd memtier_benchmark
    autoreconf -ivf
    ./configure
    make $(nproc)
    sudo make install
popd
