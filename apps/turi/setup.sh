#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pushd ${SCRIPT_DIR}

    sudo python -m pip install -U turicreate

    # Get dataset
    # We need he ASU Twitter dataset
    # https://archive.org/details/asu_twitter_dataset
    echo Downloading Twitter dataset
    wget https://archive.org/download/asu_twitter_dataset/Twitter-dataset.zip
    unzip Twitter-dataset.zip

popd
