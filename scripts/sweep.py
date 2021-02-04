# Copyright © 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import logging, os, time, subprocess, math, json, pdb, multiprocessing, random
from concurrent.futures.thread import ThreadPoolExecutor

from apps import *

###############
cur_dir = os.path.dirname(os.path.abspath(__file__))
###############

#############################################
base_output_dir = cur_dir + "/../logs/"
test_script_base = cur_dir + "/../apps/"

is_dry_run = False
runs = range(0, 5)
runs = [0]

is_local_exec = True
sims = [
    "cachegrind",
]
simulator = sims[0]

cache_max_size = 1024*1024*1024*1024
cache_min_size = 0
exp_groups = {
    # "test": {
    #     "apps" : ["turi"],
    #     "cache_perc_list" : [2.5],
    #     "block_sizes" : [4*1024],
    #     "assocs" : [4],
    # },
    "sizes": {
        "apps" : ["redis", "metis", "turi"],
        "cache_perc_list" : [2.5, 1.0, 0.75, 0.5, 0.25, 0.1, 0.05, 0.02, 0.01, 0.005],
        "block_sizes" : [4*1024],
        "assocs" : [4],
    },
    "blocks": {
        "apps" : ["redis"],
        "cache_perc_list" : [1.0, 0.5, 0.25, 0.005],
        "block_sizes" : [4*1024, 64, 256, 512, 1*1024, 8*4*1024],
        "assocs" : [4],
    }
}

#############################################

def profile_to_str(profile, simulator):
    # SIMULATOR=${1}
    # UNIQUE_ID=${2}
    # CACHE_PARAMS=${3}
    # OUTPUT_PREFIX=${4}
    # METHOD=${5}

    log_prefix="{}/{}/sim-{}-method-{}-config-{}-run-{}".format(
                                    base_output_dir,
                                    profile["dir"],
                                    simulator,
                                    profile["method"],
                                    profile["cache_config"],
                                    profile["run"])

    if "mem" in profile:
        params = "{}".format(profile["mem"])
    elif "I1" in profile:
        params = " '--I1={}  --D1={} --L2={}' ".format( 
                                        profile["I1"],
                                        profile["D1"],
                                        profile["L2"])

    cmd = "/usr/bin/time -v {} {} {} {} {} {} > {} 2>&1 ".format(
                    test_script_base + "/" + profile["dir"] + "/test.sh",
                    simulator,
                    (profile["unique_id"]),
                    params,
                    log_prefix,
                    profile["method"],
                    log_prefix + ".test.out"
                    )

    os.system("mkdir -p " + os.path.dirname(log_prefix))

    print (cmd)
    return cmd


def run_profile(profile, simulator, is_dry_run):
    cmd = profile_to_str(profile, simulator)

    logging.info("Calling: " + cmd)
    if not is_dry_run:
        subprocess.call(cmd, shell=True)
    logging.info("Complete: " + cmd)


def get_cache_size(peak_mem, exp, do_round_to_2 = True):
    max_size = cache_max_size
    min_size = cache_min_size

    cache_sizes = []
    for x in exp["cache_perc_list"]:
        size = x * peak_mem

        if do_round_to_2:
            # pow_2 = pow(2, math.ceil(math.log(size)/math.log(2)))  # round up
            pow_2 = pow(2, round(math.log(size)/math.log(2)))  # round off

            # Check if this number already exists in combinations
            if pow_2 in cache_sizes:
                logging.info("cache size={} rounded to pow_2={} which is already in list".format(
                                size, pow_2))
                continue
            else:
                size = pow_2

        if size >= max_size:
            logging.info("size={} must be < max_size={}".format(size, max_size))
            continue

        if size < min_size:
            logging.info("size={} must be > min_size={}".format(size, min_size))
            continue

        cache_sizes.append(size)

    return cache_sizes

def get_cache_configs(peak_mem, num_cores, simulator, exp, l1_to_l3=True, beyond_l3=True):
    configs = []

    # Cachegrind cache configs
    #######################

    if l1_to_l3:
        # L1 & L2
        configs.append({"I1"            : "32768,8,64",
                        "D1"            : "32768,8,64",
                        "L2"            : "65536,16,64",
                        "cache_config"  : "l2"})

        # # L1 & L3
        # Assume 16 ways instead of 11 - with the same line size
        # size = 1.375MB, assume 2MB per core
        # Calculate CPU count considering Hyperthreading
        cpu_count = multiprocessing.cpu_count() / 2

        # The max L3 we can give = number of cores on system * L3 per core
        if num_cores > cpu_count:
            num_cores = cpu_count

        size_raw = num_cores * 1.375 * 1024 * 1024
        size = pow(2, round(math.log(size_raw)/math.log(2)))  # round off
        config_name = "l3"

        logging.info ("L3={}, rounded off={}".format(size_raw, size))
        configs.append({"I1"            : "32768,8,64",
                        "D1"            : "32768,8,64",
                        "L2"            : str(size) + ",16,64",
                        "cache_config"  : config_name})

    # Move on beyond L3 now
    #######################

    if beyond_l3:

        cache_sizes = get_cache_size(peak_mem, exp)

        logging.info ("cache_sizes=" + str(cache_sizes))
        logging.info ("block_sizes=" + str(exp["block_sizes"]))
        logging.info ("assocs=" + str(exp["assocs"]))

        block_mem_pairs = []

        for size in cache_sizes:
            for block in exp["block_sizes"]:
                for assoc in exp["assocs"]:
                    block_mem_pairs.append( {"cache_size": size, "block_size": block, "assoc": assoc} )

        logging.info("block_mem_pairs=" + str(block_mem_pairs))

        for pair in block_mem_pairs:
            configs.append({"I1"            : "32768,8,64",
                            "D1"            : "32768,8,64",
                            "L2"            : "{},{},{}".format(pair["cache_size"], pair["assoc"], pair["block_size"]),
                            "cache_config"  : "size={}*block={}*assoc={}".format(pair["cache_size"], pair["block_size"], pair["assoc"])})

    return configs

def get_apps_profiles(apps, simulator, runs, exp, counter):

    profiles_all = dict()
    for a, details in apps.items():
        logging.info("Getting {} profiles".format(a))
        profiles = []

        peak_mems, num_cores = get_mem_and_cores_info(a)

        for r in runs:
            for m in details["methods_valid"]:
                logging.info("{}, method={}".format(a, m))

                base = get_cache_configs(peak_mems[m], num_cores[m], simulator, exp, True, False)

                for c in (base + get_cache_configs(peak_mems[m], num_cores[m], simulator, exp, False, True)):
                    profile = {
                        "dir"           : details["dir"],
                        "method"        : m,
                        "unique_id"     : (len(profiles) + counter),
                        "run"           : r,
                    }
                    profile.update(c)
                    profiles.append(profile)

                    counter += 1

        profiles_all[a] = profiles

    return (profiles_all, counter)

def setup_logging(log_filename):

    if os.path.dirname(log_filename):
        os.system("mkdir -p " + os.path.dirname(log_filename))

    logFormatter = logging.Formatter("[%(asctime)s][%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    
    fileHandler = logging.FileHandler(log_filename + ".log", mode='w')
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.INFO)
    rootLogger.addHandler(fileHandler)
    
    fileHandler_debug = logging.FileHandler(log_filename + ".debug.log", mode='w')
    fileHandler_debug.setFormatter(logFormatter)
    fileHandler_debug.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler_debug)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)

    rootLogger.info("Logging setup: " + log_filename)

if __name__ == "__main__":
    
    logfile = cur_dir + "/../logs/sweep"
    setup_logging(logfile)

    profiles = {}
    counter = 0
    for ee in exp_groups:
        select_apps = {}
        for aa in exp_groups[ee]["apps"]:
            select_apps[aa] = apps[aa]

        (new_profs, counter) = get_apps_profiles(select_apps, simulator, runs, exp_groups[ee], counter)
        for aa_new in new_profs:
            if aa_new not in profiles:
                profiles[aa_new] = []
            profiles[aa_new] = profiles[aa_new] + new_profs[aa_new]

    logging.info(profiles)

    logging.info("*************************************")
    logging.info("Executing: ")
    logging.info("*************************************")

    executor = ThreadPoolExecutor(max_workers=32)

    with executor:
        futures = []
        for app in profiles:
            for p in profiles[app]:
                logging.info("Submitting: " + str(p))
                futures.append(executor.submit(run_profile, p, simulator, is_dry_run))

        logging.info("Exiting")
