# KCacheSim

## Instructions
These instructions have been tested on a clean Ubuntu 20.04 installation running on a CloudLab C6420 machine.
Make sure you have sudo access and at least 100GB free space for application datasets and logs.

Clone the repository and submodules
```
git clone --recurse-submodules https://github.com/project-kona/KCacheSim.git
cd KCacheSim
```

Install dependencies
```
./scripts/setup.sh
```

Run everything (this will take a long time and it is best to launch this inside a screen session)
```
python3 ./scripts/sweep.py
```
All logs will be generated in `logs` directory

Finally, generate all plots
```
python3 ./scripts/gather-results.py
```
All plots will be generated in `plots` directory.

Note: Logs and plots from a sample run are stored in `saved-data`
