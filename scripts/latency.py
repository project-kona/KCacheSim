import os, csv

###
## Note: All latencies should be returned in nanoseconds!
###

###############
cur_dir = os.path.dirname(os.path.abspath(__file__))
###############

def get_rdma_latency():
    # Latency CSV files path
    read_filename  = cur_dir + "/rdma-read-lats.csv"
    write_filename = cur_dir + "/rdma-write-lats.csv"

    rdma_lats = dict()
    rdma_lats["r"] = dict()
    rdma_lats["w"] = dict()

    # We want to use t_avg field from CSV
    # Convert usec to nanoseconds

    with open(read_filename, 'r', encoding="utf-8-sig") as file:
        csv_file = csv.DictReader(file)
        for row in csv_file:
            rdma_lats["r"][int(row['#bytes'])] = float(row['t_avg[usec]']) * 1000

    with open(write_filename, 'r', encoding="utf-8-sig") as file:
        csv_file = csv.DictReader(file)
        for row in csv_file:
            rdma_lats["w"][int(row['#bytes'])] = float(row['t_avg[usec]']) * 1000

    return rdma_lats

# Read RDMA latency from file and store it.
RDMA_LATENCY = get_rdma_latency()


def get_remote_latency(access_size, remote_type, access_type='r'):
    if remote_type ==  "pberry": 
        # needs get_rdma_latency() to be set
        # TODO: get pberry latency
        if access_type == 'r':
            return RDMA_LATENCY['r'][access_size]
        else:
            return RDMA_LATENCY['w'][access_size]

    # 40 us (infiniswap), 10 us (regions), 9.7us (legoos)
    elif remote_type == "infiniswap":
        return 40 * 1000

    elif remote_type == "regions":
        return 10 * 1000

    elif remote_type == "legoos":
        return 10 * 1000


def get_cache_latency(access_size, cache_type):
    # independant of access size

    # measured main memory on a vmware Skylake server:
    # Main (SW only setup) 82 ns
    # Numa (pberry setup) 130 ns

    if cache_type == "main":
        return 82
    elif cache_type == "numa":
        return 130
    else:
        return -1


def get_l1_to_l3_latency(access_size):
    # independant of access size

    # Reference:
    # https://www.anandtech.com/show/11544/intel-skylake-ep-vs-amd-epyc-7000-cpu-battle-of-the-decade/13
    # Freq = 2 Ghz
    #
    # L1 4 cycles (2ns)
    # L2 18 cycles (9ns)
    # L3 26 ns
    lats = {
        "L1"    : 2,
        "L2"    : 9,
        "L3"    : 26,
    }

    return lats
