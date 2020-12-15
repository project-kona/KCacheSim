# KCacheSim

## Instructions
sudo apt-get update

pushd valgrind

./autogen.sh && \
./configure --prefix=$(pwd)/build/ && \
make -j$(nproc) && \
make install

popd

