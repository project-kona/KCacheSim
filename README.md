# KCacheSim

Details about KCacheSim are in the ASPLOS 2021 paper: [Rethinking Software Runtimes for Disaggregated Memory](https://asplos-conference.org/abstracts/asplos21-paper210-extended_abstract.pdf).   
The artifacts and instructions are available from: [asplos21-ae](https://github.com/project-kona/asplos21-ae).

## Description

KCacheSim is a demand paging simulator built on top of [Cachegrind](https://valgrind.org/docs/manual/cg-manual.html).
It simulates a 4-level inclusive cache hierarchy consisting of CPU caches (L1, L2, and L3) followed by local cache (DRAM) leading to remote memory.
KCacheSim highlights the demand paging behavior of applications to inform design parameters of local cache for remote memory.

As Cachegrind can only simulate two levels of cache, KCacheSim performs multiple runs of the same applications.
First run simulates L1 and L2, the next one simulates L1 and L3, which is followed by multiple runs of L1 and the local cache with different parameters.
Our [fork of Cachegrind](https://github.com/project-kona/valgrind) expands the 1GB maximum cache size limit of Cachegrind.
KCacheSim uses cache miss rates and total memory accesses metrics at each cache level to caculate the overall Average Memory Access Time (AMAT) for an application running on a specified 4-level cache hierarchy.
We use the sensitivity of AMAT to local cache parameters (cache size, block size and associativity) to inform the design of DRAM cache in a remote memory system.

## Instructions

These instructions have been tested on a clean Ubuntu 20.04 installation running on a CloudLab C6420 machine.
Make sure you have sudo access and at least 128GB RAM and 100GB free space for application datasets and logs.

Before following these instructions, make sure you have installed the applications by following 
instructions from https://github.com/project-kona/apps.

Clone the repository and submodules
```
git clone --recurse-submodules https://github.com/project-kona/KCacheSim.git
cd KCacheSim
```

Install dependencies
```
./scripts/setup.sh
```

Run everything (this will take a long time and it is best to launch this inside a `screen` session)
```
python3 ./scripts/sweep.py
```
All logs will be generated in `logs` directory

Finally, generate all plots
```
python3 ./scripts/gather-results.py
```
All plots will be generated in `plots` directory.

## Access Latency Values
The access times for CPU caches (L1, L2, and L3), local cache (DRAM - local or across NUMA node), and remote memory are configurable in KCacheSim. Refer to `scripts/latency.py` and `scripts/rdma-*-lats.csv` to change these values.
You only need to re-run `./scripts/gather-results.py` for new latency values to take affect.

## Running Arbritary Applications with KCacheSim
KCacheSim supports any applications which can run on Cachegrind.
To add a new application KCacheSim infrastructure:
1. Measure the application peak Resident Set Size (RSS), peak Virtual Memory (VM), and number of threads/cores.
2. Add a new entry in `apps` dictionary in `scripts/apps.py` with application information.
2. Modify `scripts/sweep.py` to include new application name in `exp_groups` dictionary.
3. Create a new directory with application name in [apps](https://github.com/project-kona/apps) repository. This repository is a submodule of [asplos21-ae](https://github.com/project-kona/asplos21-ae).
4. Use `apps/turi/test.sh` as a template to generate a new `test.sh` for new application.
5. Run `scripts/sweep.py`
