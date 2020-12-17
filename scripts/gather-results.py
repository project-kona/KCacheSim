import logging, os, time, subprocess, glob
from os import listdir
from os.path import isfile, join
from pprint import pformat
import subprocess, copy

import logging
from collections import OrderedDict

from latency import *
from apps import *
from plot import *

###############
cur_dir = os.path.dirname(os.path.abspath(__file__))
###############

def setup_logging(log_filename):

    if os.path.dirname(log_filename):
        os.system("mkdir -p " + os.path.dirname(log_filename))

    logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
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

    rootLogger.info("Logging setup")

    logging.getLogger("requests").setLevel(logging.WARNING)

###########################################
def tail(f, n):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines


###########################################
def calc_amat (msr, access_size, read_write_ratio, layout, optional_data=None):

    lats = get_l1_to_l3_latency(access_size)

    # We want to account for cache accesss latency by default.
    no_cache_lat = False

    if layout == "pberry":
        # optional_data
        #   0 = Use numa latency (default)
        #   1 = Use 1 * main latency
        #   5 = Use 5 * main latency
        optional_data = optional_data if optional_data is not None else 0

        latency_to_use = 0
        if optional_data == 0:
            latency_to_use = get_cache_latency(access_size, "numa")
        else:
            latency_to_use = get_cache_latency(access_size, "main") * optional_data

        lats.update({
            "cache" : latency_to_use,
            "Remote-RD" : get_remote_latency(access_size, "pberry"),
            "Remote-WR" : get_remote_latency(access_size, "pberry"),
        })

        # For remote, we only want different read/write latencies for
        # pberry with 0% cache size.
        # We consider there is no cache when all misses of L3 are misses of cache as well.
        if (msr["cache"] == msr["L3"]):
            lats["Remote-WR"] = get_remote_latency(access_size, "pberry", 'w')
            no_cache_lat = True

    elif layout == "infiniswap":
        lats.update({
            "cache" : get_cache_latency(access_size, "main"),
            "Remote-RD" : get_remote_latency(access_size, "infiniswap"),
            "Remote-WR" : get_remote_latency(access_size, "infiniswap"),
        })

    elif layout == "regions":
        lats.update({
            "cache" : get_cache_latency(access_size, "main"),
            "Remote-RD" : get_remote_latency(access_size, "regions"),
            "Remote-WR" : get_remote_latency(access_size, "regions"),
        })

    elif layout == "legoos":
        lats.update({
            "cache" : get_cache_latency(access_size, "main"),
            "Remote-RD" : get_remote_latency(access_size, "legoos"),
            "Remote-WR" : get_remote_latency(access_size, "legoos"),
        })

    elif layout == "lats-sweep":
        # optional_data = remote latency
        # this will allow sweeps
        lats.update({
            "cache" : get_cache_latency(access_size, "main"),
            "Remote-RD" : optional_data,
            "Remote-WR" : optional_data,
        })

    # logging.info("block_size=" + str(access_size) + " Lats=" + pformat(lats))

    amats = [None] * 2

    for i in range (0, 2):
        amats[i] =(lats["L1"] + msr["L1"][i] * lats["L2"] +
                                msr["L2"][i] * lats["L3"] +
                                msr["L3"][i] * (0 if no_cache_lat else lats["cache"]) +
                                msr["cache"][i] * (lats["Remote-RD"] if i == 0 else lats["Remote-WR"]))

    # amat = amats[0]
    # amat = amats[1]
    amat = (amats[0]*read_write_ratio + amats[1]) / (1+read_write_ratio)

    logging.debug("Miss Rates = {}, \nLatency = {}, \nAMATs = {}< \nAMAT = {}, \naccess_size = {}".format(
                    pformat(msr), pformat(lats), pformat(amats), amat, access_size))
    return amat


###########################################
def extract_cache_results(path, simulator, method_props):
    # Sample File contents
    #
    # ==93336== I   refs:      314,700,018,776
    # ==93336== I1  misses:        398,550,901
    # ==93336== LLi misses:         97,075,518
    # ==93336== I1  miss rate:            0.13%
    # ==93336== LLi miss rate:            0.03%
    # ==93336== 
    # ==93336== D   refs:      122,941,883,083  (87,180,499,809 rd   + 35,761,383,274 wr)
    # ==93336== D1  misses:      1,200,918,826  (   845,773,442 rd   +    355,145,384 wr)
    # ==93336== LLd misses:      1,185,758,474  (   833,753,597 rd   +    352,004,877 wr)
    # ==93336== D1  miss rate:             1.0% (           1.0%     +            1.0%  )
    # ==93336== LLd miss rate:             1.0% (           1.0%     +            1.0%  )
    # ==93336== 
    # ==93336== LL refs:         1,599,469,727  ( 1,244,324,343 rd   +    355,145,384 wr)
    # ==93336== LL misses:       1,282,833,992  (   930,829,115 rd   +    352,004,877 wr)
    # ==93336== LL miss rate:              0.3% (           0.2%     +            1.0%  )

    lines = tail(path + "/" + f, 16)

    vals = dict()
    for l in lines:
        l = l.decode("utf-8") 
        # logging.info (l)
        parts = l.split(" ")
        temp = []
        for p in parts:
            if p:
                temp.append(p)
        parts = temp

        # Find num of data reads and writes
        if l.find("D   refs") != -1:
            vals["num_reads"] = float(parts[-5].strip().strip('()').replace(',', ''))
            vals["num_writes"] = float(parts[-2].strip().strip('()').replace(',', ''))

        if l.find("D1  misses") != -1:
            vals["d1_miss_rd_num"] = float(parts[-5].strip().strip('()').replace(',', ''))
            vals["d1_miss_wr_num"] = float(parts[-2].strip().strip('()').replace(',', ''))

            vals["d1_miss_rd"] = vals["d1_miss_rd_num"] / vals["num_reads"]
            vals["d1_miss_wr"] = vals["d1_miss_wr_num"] / vals["num_writes"]

        if l.find("LLd misses") != -1:
            vals["dll_miss_rd_num"] = float(parts[-5].strip().strip('()').replace(',', ''))
            vals["dll_miss_wr_num"] = float(parts[-2].strip().strip('()').replace(',', ''))

            vals["dll_miss_rd"] = vals["dll_miss_rd_num"] / vals["num_reads"]
            vals["dll_miss_wr"] = vals["dll_miss_wr_num"] / vals["num_writes"]

    logging.debug (pformat(vals))

    # Uncomment if we want to read raw number of reads and writes
    # method_props["raw"][simulator]["d1_miss_rd"].append(vals["d1_miss_rd"])
    # method_props["raw"][simulator]["d1_miss_wr"].append(vals["d1_miss_wr"])

    method_props["raw"][simulator]["num_reads"] = vals["num_reads"]
    method_props["raw"][simulator]["num_writes"] = vals["num_writes"]

    if config == "l2":
        # Read off L1 and L2 rates
        method_props["miss_rates"][simulator]["L1"] = (vals["d1_miss_rd"], vals["d1_miss_wr"])
        method_props["miss_rates"][simulator]["L2"] = (vals["dll_miss_rd"], vals["dll_miss_wr"])

        # Save num reads to writes ratio
        method_props["read_write_ratio"][simulator] = vals["num_reads"]/vals["num_writes"]

    elif config == "l3":
        # Read off L3
        # New L3 config where L3 is per core * num of cores used by app
        method_props["miss_rates"][simulator]["L3"] = (vals["dll_miss_rd"], vals["dll_miss_wr"])

    if type(config) is dict:
        # We have block size and total mem size.
        # Get percentage of peak app mem
        # We can also send absolute memory value instead of percentage
        if perc_peak_mem:
            perc = config["size"] / method_props["peak_mem"] * 100
        else:
            perc = config["size"] / method_props["peak_rss"] * 100
        # perc = config["size"]
        block = config["block"]
        assoc = config["assoc"]

        current_cache_dict = method_props["miss_rates"][simulator]["cache"]
        if assoc not in current_cache_dict:
            current_cache_dict[assoc] = dict()

        if perc not in current_cache_dict[assoc]:
            current_cache_dict[assoc][perc] = {"blocks": dict()}

        current_cache_dict[assoc][perc]["blocks"][block] = (vals["dll_miss_rd"], vals["dll_miss_wr"])

    return 

###########################################

def parse_one_cache_sim_results(apps, simulator):
    # AMAT Calculation
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            logging.info("AMAT: " + app + " " + props["name"])

            miss_rates_D = props['miss_rates'][simulator]
            read_write_ratio = props['read_write_ratio'][simulator]

            amats = {
                "pberry" :          {'cache' : dict()},
                "pberry-main" :     {'cache' : dict()},
                "pberry-2x-main" :  {'cache' : dict()},
                "pberry-3x-main" :  {'cache' : dict()},
                "pberry-4x-main" :  {'cache' : dict()},
                "pberry-5x-main" :  {'cache' : dict()},
                "infiniswap" :      {'cache' : dict()},
                "regions" :         {'cache' : dict()},
                "legoos" :          {'cache' : dict()},
                "lats-sweep" :      dict(),
            }

            caches = miss_rates_D['cache']

            for (assoc, assoc_details) in caches.items():
                for (perc, details) in assoc_details.items():

                    #######
                    # Pberry amats
                    for (b, rate) in details['blocks'].items():

                        msr = {
                            'L1' : miss_rates_D["L1"],
                            'L2' : miss_rates_D["L2"],
                            'L3' : miss_rates_D["L3"],
                            'cache' : rate
                        }

                        ## Function used in try/catch ahead
                        def add_amat_to_dict(amat, current_cache_dict):

                            if assoc not in current_cache_dict:
                                current_cache_dict[assoc] = dict()

                            if perc not in current_cache_dict[assoc]:
                                current_cache_dict[assoc][perc] = {"blocks": dict()}

                            current_cache_dict[assoc][perc]["blocks"][b] = amat
                        ##

                        try:
                            # access_size = block size
                            amat = calc_amat(msr, b, read_write_ratio, "pberry")
                            add_amat_to_dict (amat, amats['pberry']['cache'])

                            # Same stuff with pberry-main
                            amat = calc_amat(msr, b, read_write_ratio, "pberry", 1)
                            add_amat_to_dict (amat, amats['pberry-main']['cache'])

                            # # Even more stuff with pberry-5x-main
                            amat = calc_amat(msr, b, read_write_ratio, "pberry", 5)
                            add_amat_to_dict (amat, amats['pberry-5x-main']['cache'])

                            amat = calc_amat(msr, b, read_write_ratio, "pberry", 4)
                            add_amat_to_dict (amat, amats['pberry-4x-main']['cache'])

                            amat = calc_amat(msr, b, read_write_ratio, "pberry", 3)
                            add_amat_to_dict (amat, amats['pberry-3x-main']['cache'])

                            amat = calc_amat(msr, b, read_write_ratio, "pberry", 2)
                            add_amat_to_dict (amat, amats['pberry-2x-main']['cache'])

                        except KeyError:
                            pass

            for (assoc, assoc_details) in caches.items():
                for (perc, details) in assoc_details.items():

                    ########
                    # SW only amats
                    # We only need 4k block size for SW only layouts
                    b = 4096
                    try:
                        # The 0% cache configuration will fail for this lookup
                        rate = details['blocks'][b]
                    except:
                        continue

                    msr = {
                        'L1' : miss_rates_D["L1"],
                        'L2' : miss_rates_D["L2"],
                        'L3' : miss_rates_D["L3"],
                        'cache' : rate
                    }

                    try:
                        # access_size = block size
                        current_cache_dict = amats['infiniswap']['cache']
                        if assoc not in current_cache_dict:
                            current_cache_dict[assoc] = dict()

                        current_cache_dict = amats['regions']['cache']
                        if assoc not in current_cache_dict:
                            current_cache_dict[assoc] = dict()

                        current_cache_dict = amats['legoos']['cache']
                        if assoc not in current_cache_dict:
                            current_cache_dict[assoc] = dict()

                        amats['infiniswap']['cache'][assoc][perc] = calc_amat(msr, b, read_write_ratio, "infiniswap")
                        amats['regions']['cache'][assoc][perc] = calc_amat(msr, b, read_write_ratio, "regions")
                        amats['legoos']['cache'][assoc][perc] = calc_amat(msr, b, read_write_ratio, "legoos")
                    except KeyError:
                        pass


            # Get NUMA overheads
            assoc = 4
            block = 4096
            pberry_main = amats['pberry-main']['cache'][assoc]
            pberry = amats['pberry']['cache'][assoc]

            perc = None
            for k in pberry.keys():
                if k > 1.0:
                    perc = k
                    break

            diff = pberry[perc]['blocks'][block] - pberry_main[perc]['blocks'][block]
            props['numa_overhead'][simulator] = diff / pberry_main[perc]['blocks'][block] * 100

            logging.info("{}-method-{} - pberry={}, pberry_main={}, diff={}, numa={}".format(
                app, method, pberry[perc]['blocks'][block], pberry_main[perc]['blocks'][block],
                diff, props['numa_overhead'][simulator]))



            ########
            # SW only amats
            # We only need 4k block size for SW only layouts
            # We only need 75% or less cache size
            # Sweep latency times
            perc_target = 75
            assoc = 4
            cur_rates = caches[assoc]
            nearest_perc_details = cur_rates.get(perc_target, cur_rates[min(cur_rates.keys(), key=lambda k: abs(k-perc_target))])
            rate = nearest_perc_details['blocks'][4096]
            # TODO Verify this rate and nearest perc calculation
            msr = {
                'L1' : miss_rates_D["L1"],
                'L2' : miss_rates_D["L2"],
                'L3' : miss_rates_D["L3"],
                'cache' : rate
            }

            lats_sweep_list = [x*1000 for x in [3, 6, 10, 16, 24, 32, 40]]
            try:
                # access_size = block size
                for l in lats_sweep_list:
                    amats['lats-sweep'][l] = calc_amat(msr, b, read_write_ratio, "lats-sweep", l)
            except KeyError:
                pass

            # Save results
            props["AMATs"][simulator] = amats


###########################################
if __name__ == "__main__":
    
    logfile = cur_dir + "/../logs/gather-results"
    setup_logging(logfile)

    # Start Gathering results
    logging.info(pformat(RDMA_LATENCY))

    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            props["miss_rates"] = {
                    "callgrind" :   {"cache": dict()},
                    "cachegrind" :  {"cache": dict()},
                }
            props["AMATs"] = { 
                    "callgrind" :   dict(),
                    "cachegrind" :  dict(),
                }
            props["raw"] = {
                    "callgrind" :   {"d1_miss_rd": [], "d1_miss_wr": []},
                    "cachegrind" :  {"d1_miss_rd": [], "d1_miss_wr": []},
                }
            props["read_write_ratio"] = { 
                    "callgrind" :   0,
                    "cachegrind" :  0,
                }
            props["numa_overhead"] = { 
                    "callgrind" :   0,
                    "cachegrind" :  0,
                }


    simulators = ["cachegrind", "callgrind"]

    for (app, methods) in apps.items():
        logging.info("Looking at " + app)
        path = "{}/../logs/{}/".format(cur_dir, app)

        try:
            files = [f for f in listdir(path) if (isfile(join(path, f) ))]
            for f in files:
                if not (f.endswith("cachegrind.out") or f.endswith("callgrind.out")) :
                    continue

                logging.info("Working on: " + app + " - " + f)

                parts = f.split(".")
                parts = parts[0].split("-")

                sim = parts[1]
                method = parts[3]

                if method not in methods["methods"]:
                    logging.info("Ignoring app={} - method={} because it is not in apps.py".format(app, method))
                    continue


                if sim not in simulators:
                    logging.info("Ignoring sim={} because it is not in simulators list".format(sim))
                    continue

                if parts[5] in ["l2", "l3"]:
                    config = parts[5]
                else:
                    # This a string of format: size=1073741824*block=256*assoc=1024
                    config_parts = parts[5].split("*")
                    sizes = config_parts[0].split("=")
                    blocks = config_parts[1].split("=")

                    assoc = config_parts[2].split("=")

                    config = {
                                "size": int(sizes[1]),
                                "block": int(blocks[1]),
                                "assoc": int(assoc[1]),
                            }

                logging.debug("Name = " + methods["methods"][method]["name"] + ", Config = " + str(config) + ", Simulator = " + sim)
                extract_cache_results (path, sim, methods["methods"][method])

        except FileNotFoundError:
            logging.error("output.final directory not found for app: " + app)

    # logging.info("\n" + pformat(apps))

    # Any modifications to miss rates loaded from files
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            logging.debug("Modifying App={}, method={}".format(app, method))

            miss_rates_D = props['miss_rates']["cachegrind"]

            # Infinite cache size (beyond last point). This simulates no remote memory. No misses at cache
            if add_infinite_cache:
                for (assoc, details) in miss_rates_D['cache'].items():
                    max_perc = max(k for k, v in details.items())
                    miss_rates_D['cache'][assoc][(max_perc*1.1)] = {'blocks': {4096: (0,0)}}

            # Zero cache size is like cache does not exist - miss rate(cache) = miss rate (L3)
            for assoc in miss_rates_D['cache']:
                miss_rates_D['cache'][assoc][0] = {'blocks': {64: miss_rates_D['L3']}}

            # No L3 configuration
            # NOTE: This code is stale now
            # Everything missing L2 misses L3 as well.
            # miss_rates_D['L3'] = miss_rates_D['L2']

            # Add 0% cache point in 4k lines plot as well
            # NOTE: This code is stale now
            # miss_rates_D['cache'][0] = {'blocks': {4096: miss_rates_D['L3']}}

            # methods[method]["raw"]["d1_miss_rd_cov"] = statistics.stdev(methods[method]["raw"]["d1_miss_rd"]) / statistics.mean(methods[method]["raw"]["d1_miss_rd"])
            # methods[method]["raw"]["d1_miss_wr_cov"] = statistics.stdev(methods[method]["raw"]["d1_miss_wr"]) / statistics.mean(methods[method]["raw"]["d1_miss_wr"])

    # logging.info("\n" + pformat(apps))

    parse_one_cache_sim_results(apps, "cachegrind")

    logging.info("\n" + pformat(apps))

    plot (cur_dir + "/../plots/", apps)
