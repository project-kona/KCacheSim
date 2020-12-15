import multiprocessing

APPS = {

    # Num threads = 4 in Redis
    "redis" : {
               "dir"          : "redis",
               "process_name" : "redis-server",
               "methods_valid": ["rand"],
               "methods": {
                    "rand" : {"name": "Memtier+Redis -R:R",
                         "pretty_name" : "Redis - Random",
                         "peak_mem": 4*1024*1024*1024,
                         "num_cores": 4,
                         "peak_rss": 3855648 *1024,   # ~3.8GB
                         },
               },
        },

    # Metis
    # Num cores set in Metis = num of cores on machines
    # Hence we get all the L3.
    # Update: We have now set Metis code to run on 8 cores
    "metis" : {
               "dir"          : "metis",
               "process_name" : "XX",
               "methods_valid": ["linreg"],

               "methods": {
                    "linreg" : {"name": "Linear Regression - 40GB",
                         "pretty_name" : "Linear Regression",
                         "peak_mem": 40*1024*1024*1024,
                         "num_cores": 8,
                         "peak_rss": 40963768 *1024,   # ~40GB
                         },
               },
        },

    # Graph Processing
    # [pagerank=3GB/connectedcomp=8.4GB/labelprop=3.5/graphcol=7.2]
    #
    # From observation: Num threads = OMP_NUM_THREADS + 4
    # Consider 4 threads as initial setup and control threads and use
    # num_cores = OMP_NUM_THREADS = 10 in current setup.
    "turi" : {
                "dir"          : "turi",
                "process_name" : "XX",
                "methods_valid": ["graphcol"],

               "methods": {
                    "graphcol" : {"name": "Twitter - Graph Col.",
                         "pretty_name" : "Graph Coloring",
                         "peak_mem": 8383840 *1024,
                         "num_cores": 10,
                         "peak_rss": 6020948 *1024,   # ~6GB
                         },
               },
        },
}

apps = APPS

def get_mem_and_cores_info(app):

    peak_mems = dict()
    num_cores = dict()
    for (m,d) in APPS[app]["methods"].items():
        peak_mems[m] = d['peak_mem']
        num_cores[m] = d['num_cores']

    return (peak_mems, num_cores)

# Calculate cache memory size as percentage of peak mem or peak RSS
perc_peak_mem = False
add_infinite_cache = False
