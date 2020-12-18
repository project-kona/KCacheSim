import chart_studio
import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
from plotly.colors import DEFAULT_PLOTLY_COLORS
import plotly.express as px
import statistics
import itertools
import six
import logging
from pprint import pformat
import json
import csv
import os

from apps import *

DEFAULT_PLOTLY_COLORS=['rgb(31, 119, 180)', 'rgb(255, 127, 14)',
                       'rgb(44, 160, 44)', 'rgb(214, 39, 40)',
                       'rgb(148, 103, 189)', 'rgb(140, 86, 75)',
                       'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                       'rgb(188, 189, 34)', 'rgb(23, 190, 207)',
                       'rgb(0, 0, 0)', 'rgb(128, 128, 128)',
                       'darkturquoise', 'darkviolet',
                       ]

def plot(filename, data):
    # plot_4k(filename + "amat-4k", data)
    # plot_4k_multi_assocs(filename + "amat-4k-multi-assoc", data)
    plot_pberry_lines(filename + "amat-pberry-block-sweep", data)
    # plot_lat_sweep(filename + "amat-lat-sweep", data)
    # plot_amat_hit(filename + "amat-vs-miss-rate", data)

    plot_4k_paper(filename + "amat-vs-rss", data)
    plot_block_sweep_paper(filename + "amat-pberry-block-sweep")

    # plot_pberry_lines_ppt(filename + "amat-pberry-block-sweep-ppt", data)
    # plot_cgroups(filename + "cgroups", data)



def plot_amat_hit(filename, data):

    titles = []
    assocs = [1024, 4]
    blocks = [4096]

    for assoc in assocs:
        titles.append("Assoc={}".format(assoc))

    # Make subplot for each associativity
    fig = make_subplots(rows=1, cols=len(assocs),
                        subplot_titles=titles)

    # fig.update_xaxes(title_text="Cache Miss Rate (%)", rangemode='tozero')
    fig.update_xaxes(title_text="Cache Miss Rate (%)", type='log', rangemode='tozero')
    fig.update_yaxes(title_text="AMAT(ns)", rangemode='tozero')
    fig.update_layout(title_text=("Pberry AMAT vs Cache miss rates. How sensitive is AMAT to cache miss rate for different apps?"))

    assoc_index = 0
    for assoc in assocs:
        app_index = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():

                miss_rates = props["miss_rates"]["cachegrind"]["cache"][assoc]

                amats = props['AMATs']['cachegrind']['pberry']['cache'][assoc]

                perc_mems = sorted(list(miss_rates.keys()))
                miss_r = []
                names = []

                # We need a list of perc values for each block with a name 
                data = dict()
                for m in perc_mems:
                    blocks_list = miss_rates[m]['blocks']
                    amat_list = amats[m]['blocks']

                    perc_data = []
                    block_keys = blocks_list.keys()
                    for k in block_keys:
                        if k not in blocks:
                            continue

                        # rr = blocks_list[k][0] + blocks_list[k][1]
                        read_write_ratio = props['read_write_ratio']["cachegrind"]
                        rr = (blocks_list[k][0]*read_write_ratio + blocks_list[k][1]) / (1+read_write_ratio)
                        perc_data.append(rr)

                        amat_val = amat_list[k]

                        pair = "b={}-a={}".format(k, assoc)
                        if pair not in data:
                            data[pair] = {'x': [], 'y': [], 'color_id': app_index}

                        data[pair]['x'].append(rr)
                        data[pair]['y'].append(amat_val)

                    miss_r.append(perc_data)
                    names.append("assoc={}".format(assoc))

                # Sorting
                for p in data[pair]:
                    list1, list2 = zip(*sorted(zip(data[pair]['x'], data[pair]['y'])))
                    list1, list2 = (list(t) for t in zip(*sorted(zip(list1, list2))))

                    data[pair]['x'] = list1
                    data[pair]['y'] = list2

                # logging.info("Original")
                # logging.info(pformat(miss_r))
                # logging.info(pformat(data))

                for (pair, points) in data.items():
                    fig.add_trace(go.Scatter(
                        # name="assoc={}, block={}".format(assoc, block),
                        name="{}-pair={}".format(props['name'], pair),
                        x=points['x'],  y=points['y'],
                        legendgroup=props['name'],
                        showlegend=True if assoc_index == 0 else False,
                        line=dict(color=DEFAULT_PLOTLY_COLORS[points['color_id']]),
                        marker=dict(symbol=points['color_id'], size=10),
                        ), 
                        col = assoc_index+1, row = 1)

                app_index += 1

        assoc_index += 1

    # To generate HTML output:
    file = filename
    pio.write_html(fig, file=file + ".html",
                        auto_open=False, include_plotlyjs="cdn")
    
    fig.write_image(file + ".pdf")
    fig.write_image(file + ".png")
    logging.info("Plot generated at: {}".format(file))




# def plot_assoc_lines(filename, data):

#     titles = []
#     assocs = []
#     for (app, methods) in apps.items():
#         for (method,props) in methods["methods"].items():
#             titles.append(props['name'])
#             assocs = props["miss_rates"]["cachegrind"]["cache"].keys()

#     fig = make_subplots(rows=2, cols=4,
#                         subplot_titles=titles)

#     fig.update_xaxes(title_text="Cache Size (% peak mem)" if perc_peak_mem else "Cache Size (% peak RSS)")
#     fig.update_yaxes(title_text="Cache Miss Rate (%)", rangemode='tozero')
#     fig.update_layout(title_text=("Assoc-Cache miss rates"))

#     for assoc in assocs:

#         subplot_count = 0
#         for (app, methods) in apps.items():
#             for (method,props) in methods["methods"].items():

#                 miss_rates = props["miss_rates"]["cachegrind"]["cache"][assoc]

#                 perc_mems = sorted(list(miss_rates.keys()))
#                 miss_r = []
#                 names = []

#                 # We need a list of perc values for each block with a name 
#                 data = dict()
#                 for m in perc_mems:
#                     blocks_list = miss_rates[m]['blocks']

#                     perc_data = []
#                     block_keys = blocks_list.keys()
#                     for k in block_keys:
#                         if k not in [4096]:
#                             continue

#                         rr = blocks_list[k][0] + blocks_list[k][1]
#                         perc_data.append(rr)

#                         pair = "b={}-a={}".format(k, assoc)
#                         if pair not in data:
#                             data[pair] = {'x': [], 'y': [], 'color_id': list(assocs).index(assoc)}

#                         data[pair]['x'].append(m)
#                         data[pair]['y'].append(rr)

#                     miss_r.append(perc_data)
#                     names.append("assoc={}".format(assoc))

#                 logging.info("Original")
#                 logging.info(pformat(miss_r))
#                 logging.info(pformat(data))


#                 # names = ["wall-time", "perf"]

#                 # hovertemplate = ('x = Memory Limit = %{x}% = %{text}MB<br>'+
#                 #                 'y = Time(s)/Perf = %{y} <br>'+
#                 #                 '%{hovertext}')

#                 # hover_infos = []
#                 # mems = []
#                 # for perc in perc_mems:
#                 #     mem = perc*props['peak_mem'] if perc_peak_mem else perc*props['peak_rss']
#                 #     mems.append(int(mem/1024/1024/100))

#                 #     hover_text = ("Peak mem = {}MB<br>" + 
#                 #                 "Peak RSS = {}MB"
#                 #                 ).format(
#                 #                         int(props['peak_mem']/1024/1024),
#                 #                         int(props['peak_rss']/1024/1024)
#                 #                         )
#                 #     hover_infos.append(hover_text)


#                 col = int(subplot_count%4)+1
#                 row = int(subplot_count/4)+1

#                 for (pair, points) in data.items():
#                     fig.add_trace(go.Scatter(
#                         # name="assoc={}, block={}".format(assoc, block),
#                         name=pair,
#                         x=points['x'],  y=points['y'],
#                         legendgroup=pair,
#                         showlegend=True if subplot_count is 0 else False,
#                         line=dict(color=DEFAULT_PLOTLY_COLORS[points['color_id']]),
#                         marker=dict(symbol=points['color_id'], size=10),
#                         # text=mems,
#                         # hovertext=hover_infos,
#                         # hovertemplate=hovertemplate,
#                         ), 
#                         col = col, row = row)

#                 subplot_count += 1

#     # To generate HTML output:
#     file = filename
#     pio.write_html(fig, file=file + ".html",
#                         auto_open=False, include_plotlyjs="cdn")
    
#     fig.write_image(file + ".pdf")
#     fig.write_image(file + ".png")
#     logging.info("Plot generated at: {}".format(file))




def plot_cgroups(filename, data):

    titles = []
    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            titles.append(props['name'])


    names = ["wall-time", "perf"]

    for i in range(2):
        fig = make_subplots(rows=2, cols=4,
                            subplot_titles=titles)

        fig.update_xaxes(title_text="Cache Size (% peak mem)" if perc_peak_mem else "Cache Size (% peak RSS)")
        fig.update_yaxes(title_text="Normalized Execution Time", rangemode='tozero')
        fig.update_layout(title_text=("Cgroups wall-time" if i == 0 else "Cgroups perf stats"))

        # We will end up with 10 combinations of app-method
        subplot_count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():

                perc_mems = sorted(list(props["cgroups-wall-time"].keys()))
                wall_times = []
                perfs = []
                infiniswap_times = []
                for m in perc_mems:
                    wall_times.append(props["cgroups-wall-time"][m])
                    perfs.append(props["cgroups-perf"][m])

                    try:
                        infiniswap_times.append(props["cgroups-infiniswap"][m])
                    except:
                        infiniswap_times.append(None)

                hovertemplate = ('x = Memory Limit = %{x}% = %{text}MB<br>'+
                                'y = Time(s)/Perf = %{y} <br>'+
                                '%{hovertext}')

                hover_infos = []
                mems = []
                for perc in perc_mems:
                    mem = perc*props['peak_mem'] if perc_peak_mem else perc*props['peak_rss']
                    mems.append(int(mem/1024/1024/100))

                    hover_text = ("Peak mem = {}MB<br>" + 
                                "Peak RSS = {}MB"
                                ).format(
                                        int(props['peak_mem']/1024/1024),
                                        int(props['peak_rss']/1024/1024)
                                        )
                    hover_infos.append(hover_text)

                if i == 0:
                    traces = ["wall-time", "infiniswap"]
                    data = [wall_times, infiniswap_times]
                else:
                    traces = ["perf"]
                    data = [perfs]


                col = int(subplot_count%4)+1
                row = int(subplot_count/4)+1

                for t in range(len(traces)):
                    fig.add_trace(go.Scatter(
                        name=traces[t], x=perc_mems,  y=data[t],
                        legendgroup=traces[t],
                        showlegend=True if subplot_count == 0 else False,
                        line=dict(color=DEFAULT_PLOTLY_COLORS[t]),
                        marker=dict(symbol=t, size=10),
                        text=mems,
                        hovertext=hover_infos,
                        hovertemplate=hovertemplate,
                        ), 
                        col = col, row = row)

                subplot_count += 1

        # To generate HTML output:
        file = filename + "-" + names[i]
        pio.write_html(fig, file=file + ".html",
                            auto_open=False, include_plotlyjs="cdn")
        
        fig.write_image(file + ".pdf")
        fig.write_image(file + ".png")
        logging.info("Plot generated at: {}".format(file))



def plot_lat_sweep(filename, data):

    fig = go.Figure()
    fig.update_layout(title="Remote Latency vs AMAT for ~75% mem peak size")

    fig.update_xaxes(title_text="Remote Latency (ns)")
    fig.update_yaxes(title_text="AMAT (ns)", rangemode='tozero')

    amats_arr = []
    latency_arr = []
    names = []

    # We will end up with 10 combinations of app-method
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            
            amats = props['AMATs']['cachegrind']['lats-sweep']

            amats_arr.append(list(amats.values()))
            latency_arr.append(list(amats.keys()))
            names.append(props['name'])


    for i in range(len(names)):
        fig.add_trace(go.Scatter(
            name=names[i], y=amats_arr[i],  x=latency_arr[i],
            ))


    # To generate HTML output:
    file = filename
    pio.write_html(fig, file=file + ".html",
                        auto_open=False, include_plotlyjs="cdn")
    
    fig.write_image(file + ".pdf")
    fig.write_image(file + ".png")
    logging.info("Plot generated at: {}".format(file))


def plot_block_sweep_paper(filename):
    basedir = os.path.dirname(filename)
    csv_file = basedir + "/amat-pberry-block-sweep-redis-rand.csv"

    axis_title_font = dict(size=11, family='Calibri', color='black')
    axis_tick_font=dict(size=12, family='Calibri', color='black')
    legend_font=dict(size=11, family='Calibri', color='black')
    subplot_title_font=dict(size=12, family='Calibri', color='black')

    lines=['solid', '5px 10px 2px 2px', 'longdash', 'dashdot']

    fig = go.Figure()

    data = []
    
    with open(csv_file) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        header = next(csvreader, None)
        for row in csvreader:
            data.append(row)

    data_t = list(map(list, zip(*data)))
    data_t = [[float(string) for string in inner] for inner in data_t]
    data_t[0] = [float(x)/1000 for x in data_t[0]]
    # pprint.pprint(data_t)
    # pprint.pprint(header)


    count = 0
    for i in range(len(header)-1):
        if header[i+1] not in ["0.0", "27.0", "54.0", "109.0"]:
            print("Skipping " + str(header[i+1]))
            continue

        if header[i+1] == "109.0":
            header[i+1] = "100.0"

        fig.add_trace(go.Scatter(
            name="{}%".format(header[i+1][:-2]), x=data_t[0],  y=data_t[i+1],
            legendgroup="group",
            showlegend=True,
            line=dict(color=DEFAULT_PLOTLY_COLORS[count+3], width=1, dash=lines[count]),
            marker=dict(symbol=i, size=5),
            ))
        count += 1

    fig.update_xaxes(   showline=True, linewidth=1, linecolor='black',
                        title_font=axis_title_font, tickfont=axis_tick_font,
                        )

    fig.update_yaxes(   rangemode='tozero',
                        showline=True, linewidth=1, linecolor='black',
                        title_font=axis_title_font, tickfont=axis_tick_font,
                        range=[0,33])

    fig.update_xaxes(title_text="Block Size (kB)")
    fig.update_yaxes(title_text="AMAT (ns)")

    fig.update_layout(
        plot_bgcolor='white',
        width=200, height=170,

        margin=dict(t=0, b=0, l=0, r=10),

        # Legend settings
        legend=dict(font=legend_font, orientation="h", traceorder='normal',
                    bordercolor="Black", borderwidth=0,
                    y=1.01, x=0.5,
                    xanchor='center', yanchor="top")
        )

    fig.write_image(filename + ".pdf")
    logging.info("Plot generated at: {}".format(filename))

def plot_pberry_lines(filename, data):

    titles = []
    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            titles.append(props['name'])
            assocs = props['AMATs']['cachegrind']['pberry']['cache'].keys()

    assocs = [4]

    for assoc in assocs:
        fig = make_subplots(rows=2, cols=4,
                            subplot_titles=titles)

        fig.update_xaxes(title_text="Block Size (bytes)")
        fig.update_yaxes(title_text="AMAT (ns)", rangemode='tozero')
        fig.update_layout(showlegend=False, title_text="Pberry - Block size sweep - assoc={}".format(assoc))

        # We will end up with 10 combinations of app-method
        subplot_count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():
                
                amats = props['AMATs']['cachegrind']['pberry']['cache'][assoc]

                amat_values = []
                names = []
                names_csv = []
                blocks_arr = []

                for perc, details in amats.items():
                    # Get list of blocks tried out in experiments
                    if (len(details['blocks']) > len(blocks_arr)):
                        blocks_arr = list(details['blocks'].keys())
                        blocks_arr.sort()

                for perc, details in amats.items():
                    new_amats_list = []

                    # NOTE: Commenting this will show cache size = 0 point as well.
                    # if len(details['blocks']) == 1:
                    #     continue

                    for b in blocks_arr:
                        try:
                            new_amats_list.append(details['blocks'][b])
                        except:
                            pass

                    mem = int(perc/100 * props['peak_rss']/1024/1024)

                    amat_values.append(new_amats_list)
                    names.append("{}MB={}%".format(mem, round(perc, 2)))
                    names_csv.append("{}".format(round(perc, 0)))

                # logging.info("names={}", str(names))

                for i in range(len(names)):
                    fig.add_trace(go.Scatter(
                        name=names[i], x=blocks_arr,  y=amat_values[i],
                        line=dict(color=DEFAULT_PLOTLY_COLORS[i]),
                        marker=dict(symbol=i, size=10),
                        ), 
                        col = int(subplot_count%4)+1, row = int(subplot_count/4)+1)

                subplot_count += 1

                # Generate CSV
                if app in ['redis'] and method in ["rand"]:
                    csv_data = []
                    csv_data.append(blocks_arr)
                    names_to_use = []
                    for i in range(len(amat_values)):
                        if (len(amat_values[i])) == len(blocks_arr):
                            csv_data.append(amat_values[i])
                            names_to_use.append(names_csv[i])

                    transpose = list(map(list, zip(*csv_data)))
                    header = names_to_use
                    header.insert(0, "blocksize")
                    transpose.insert(0, header)

                    csv_file = "{}-{}-{}.csv".format(filename, app, method)
                    with open(csv_file,"w+") as my_csv:
                        csvWriter = csv.writer(my_csv,delimiter=',')
                        csvWriter.writerows(transpose)

        # To generate HTML output:
        file = filename + "-assoc=" + str(assoc)
        pio.write_html(fig, file=file + ".html",
                            auto_open=False, include_plotlyjs="cdn")
        
        fig.write_image(file + ".pdf")
        fig.write_image(file + ".png")
        logging.info("Plot generated at: {}".format(file))

def plot_pberry_lines_ppt(filename, data):

    def app_filter(app, method):
        if ((app == "app-1" and method == 2) or
            (app == "app-2" and method == 3)):
            return True
        else:
            return False

    titles = []
    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            if not app_filter(app, method):
                continue
            titles.append(props['pretty_name'])
            assocs = props['AMATs']['cachegrind']['pberry']['cache'].keys()

    assocs = [4]

    for assoc in assocs:
        fig = make_subplots(rows=1, cols=3,
                            subplot_titles=titles)

        fig.update_xaxes(title_text="Block Size (bytes)", linecolor='black')
        fig.update_yaxes(title_text="AMAT (ns)", rangemode='tozero', linecolor='black')
        fig.update_layout(showlegend=True, title_text="Pberry - Block size sweep - assoc={}".format(assoc))

        # We will end up with XX combinations of app-method
        subplot_count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():
                if not app_filter(app, method):
                    continue

                amats = props['AMATs']['cachegrind']['pberry']['cache'][assoc]

                amat_values = []
                names = []
                blocks_arr = []

                orig_perc = list(amats.keys())
                # These tolerance and perc_list work only for the current app_filter
                tolerance = 20
                perc_list = [120, 75, 50, 25, 1]
                selected_perc = []
                for p in perc_list:
                    for perc in orig_perc:
                        if abs(perc - p) < tolerance:
                            selected_perc.append(perc)
                            orig_perc.remove(perc) 
                            break

                # print (selected_perc)

                for perc, details in amats.items():
                    if perc not in selected_perc:
                        continue

                    # Get list of blocks tried out in experiments
                    if (len(details['blocks']) > len(blocks_arr)):
                        blocks_arr = list(details['blocks'].keys())
                        blocks_arr.sort()

                for perc in sorted(list(amats.keys())):
                    if perc not in selected_perc:
                        continue
                    new_amats_list = []

                    for b in blocks_arr:
                        try:
                            new_amats_list.append(amats[perc]['blocks'][b])
                        except:
                            pass

                    mem = int(perc/100 * props['peak_rss']/1024/1024)

                    amat_values.append(new_amats_list)
                    names.append("{}MB={}%".format(mem, round(perc, 2)))

                for i in range(len(names)):
                    fig.add_trace(go.Scatter(
                        name=names[i], x=blocks_arr,  y=amat_values[i],
                        line=dict(color=DEFAULT_PLOTLY_COLORS[i]),
                        marker=dict(symbol=i, size=10),
                        ), 
                        col = int(subplot_count%3)+1, row = 1)

                subplot_count += 1

        # To generate HTML output:
        file = filename + "-assoc=" + str(assoc)
        pio.write_html(fig, file=file + ".html",
                            auto_open=False, include_plotlyjs="cdn")
        
        fig.write_image(file + ".pdf")
        fig.write_image(file + ".png")
        logging.info("Plot generated at: {}".format(file))


def get_4k_single_figure_data(props, assoc, style):

    amats = props['AMATs']['cachegrind']

    try:
        have_prefetch_results = assoc in list(props['AMATs']['callgrind']['pberry']['cache'].keys())
    except:
        have_prefetch_results = False

    infiniswap = amats['infiniswap']['cache'][assoc]
    regions = amats['regions']['cache'][assoc]
    legoos = amats['legoos']['cache'][assoc]

    pberry = dict()
    for perc, details in amats['pberry']['cache'][assoc].items():
        try:
            pberry[perc] = details['blocks'][4096]
        except:
            pass

    pberry_main = dict()
    for perc, details in amats['pberry-main']['cache'][assoc].items():
        try:
            pberry_main[perc] = details['blocks'][4096]
        except:
            pass

    pberry_5x_main = dict()
    for perc, details in amats['pberry-5x-main']['cache'][assoc].items():
        try:
            pberry_5x_main[perc] = details['blocks'][4096]
        except:
            pass

    pberry_4x_main = dict()
    for perc, details in amats['pberry-4x-main']['cache'][assoc].items():
        try:
            pberry_4x_main[perc] = details['blocks'][4096]
        except:
            pass

    pberry_3x_main = dict()
    for perc, details in amats['pberry-3x-main']['cache'][assoc].items():
        try:
            pberry_3x_main[perc] = details['blocks'][4096]
        except:
            pass

    pberry_2x_main = dict()
    for perc, details in amats['pberry-2x-main']['cache'][assoc].items():
        try:
            pberry_2x_main[perc] = details['blocks'][4096]
        except:
            pass

    if have_prefetch_results:
        pberry_prefetch = dict()
        for perc, details in props['AMATs']['callgrind']['pberry']['cache'][assoc].items():
            try:
                pberry_prefetch[perc] = details['blocks'][4096]
            except:
                pass

    # We have 4 dicts of amats now. They all have same cache_size percentages
    if style == 1:
        # Paper Plot
        names = ["LegoOS", "Kona", "Kona-main"]
        dicts_list = [legoos, pberry, pberry_main]
        # names = ["LegoOS", "Kona", "Kona-main", "Kona-5x-main", "Kona-4x-main", "Kona-3x-main", "Kona-2x-main"]
        # dicts_list = [legoos, pberry, pberry_main, pberry_5x_main, pberry_4x_main, pberry_3x_main, pberry_2x_main]
    elif style == 0:
        # Normal single associativity
        names = ["infiniswap", "pberry (4k)", "pberry-main (4k)", "pberry-5x-main", "pberry-4x-main", "pberry-3x-main", "pberry-2x-main", "LegoOS"]
        dicts_list = [infiniswap, pberry, pberry_main, pberry_5x_main, pberry_4x_main, pberry_3x_main, pberry_2x_main, legoos]

        if have_prefetch_results:
            names.append("pberry-prefetch")
            dicts_list.append(pberry_prefetch)
    elif style == 2:
        # Normal multi associativity
        names = ["pberry (4k)"]
        dicts_list = [pberry]


    # Collect other information
    amat_values = []
    perc_arrs = []
    miss_infos = []
    mem_sizes = []

    for amat_dict in dicts_list:
        percentages = list(amat_dict.keys())
        percentages.sort(reverse=True)
        perc_arrs.append(percentages)

        new_amats_list = []
        new_miss_info = []
        new_mem_sizes = []
        for perc in percentages:
            new_amats_list.append(amat_dict[perc])
            mem = perc*props['peak_mem'] if perc_peak_mem else perc*props['peak_rss']
            new_mem_sizes.append(int(mem/1024/1024/100))

            cur_miss_rate = props['miss_rates']["cachegrind"]['cache'][assoc][perc]['blocks'][4096]
            hover_text = ("<br><b>Global Cache Miss  (num_miss/num_<read/write>):</b><br>" +
                        "Read={}<br>" +
                        "Write={}<br><br>" +
                        "Peak mem = {}MB<br>" + 
                        "Peak RSS = {}MB"
                        ).format(
                                cur_miss_rate[0], cur_miss_rate[1],
                                int(props['peak_mem']/1024/1024),
                                int(props['peak_rss']/1024/1024)
                                )

            if have_prefetch_results:
                try:
                    cur_miss_rate = props['miss_rates']["callgrind"]['cache'][assoc][perc]['blocks'][4096]
                    hover_text += ("<br><br><b>Prefetch Global Cache Miss:</b><br>" + 
                        "Read={}<br>" +
                        "Write={}<br><br>").format(cur_miss_rate[0], cur_miss_rate[1])
                except:
                    pass

            new_miss_info.append(hover_text)

        amat_values.append(new_amats_list)
        miss_infos.append(new_miss_info)
        mem_sizes.append(new_mem_sizes)

    return {
            "amat_values": amat_values,
            "perc_arrs": perc_arrs,
            "names": names,
            "mem_sizes": mem_sizes,
            "miss_infos": miss_infos,
            }


def plot_4k(filename, data):

    titles = []
    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            titles.append(props['name'])
            assocs = props['AMATs']['cachegrind']['pberry']['cache'].keys()

    for assoc in assocs:

        fig = make_subplots(rows=2, cols=4,
                            subplot_titles=titles)

        fig.update_xaxes(title_text="Cache Size (% peak mem)" if perc_peak_mem else "Cache Size (% peak RSS)")
        fig.update_yaxes(title_text="AMAT (ns)", rangemode='tozero')
        fig.update_layout(title_text="SW vs HW AMATs - block size = 4k - assoc = {}".format(assoc))

        # We will end up with 10 combinations of app-method
        subplot_count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():

                data = get_4k_single_figure_data (props, assoc, 0)

                hovertemplate = ('x = Cache Size = %{x}% = %{text}MB<br>'+
                                'y = AMAT (ns) = %{y}ns<br>'+
                                '%{hovertext}')

                for i in range(len(data["names"])):
                    col = int(subplot_count%4)+1
                    row = int(subplot_count/4)+1

                    fig.add_trace(go.Scatter(
                        name=data["names"][i], x=data["perc_arrs"][i],  y=data["amat_values"][i],
                        text=data["mem_sizes"][i],
                        legendgroup=data["names"][i],
                        showlegend=True if subplot_count == 0 else False,
                        line=dict(color=DEFAULT_PLOTLY_COLORS[i]),
                        marker=dict(symbol=i, size=10),
                        hovertext=data["miss_infos"][i],
                        hovertemplate=hovertemplate,
                        ), 
                        col = col, row = row)

                subplot_count += 1

        # To generate HTML output:
        file = filename + "assoc=" + str(assoc)
        pio.write_html(fig, file=file + ".html",
                            auto_open=False, include_plotlyjs="cdn")
        
        fig.write_image(file + ".pdf")
        fig.write_image(file + ".png")
        logging.info("Plot generated at: {}".format(file))



def plot_4k_multi_assocs(filename, data):

    titles = []
    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            titles.append(props['pretty_name'])
            assocs = props['AMATs']['cachegrind']['pberry']['cache'].keys()

    fig = make_subplots(rows=2, cols=4,
                        subplot_titles=titles)

    fig.update_xaxes(title_text="Cache Size (% peak mem)" if perc_peak_mem else "Cache Size (% peak RSS)")
    fig.update_yaxes(title_text="AMAT (ns)", rangemode='tozero')
    fig.update_layout(title_text="SW vs HW AMATs - block size = 4k - Multi Associativity")

    assoc_index = 0
    for assoc in assocs:

        # We will end up with 10 combinations of app-method
        subplot_count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():

                data = get_4k_single_figure_data (props, assoc, 2)

                hovertemplate = ('x = Cache Size = %{x}% = %{text}MB<br>'+
                                'y = AMAT (ns) = %{y}ns<br>'+
                                '%{hovertext}')

                for i in range(len(data["names"])):
                    col = int(subplot_count%4)+1
                    row = int(subplot_count/4)+1

                    fig.add_trace(go.Scatter(
                        name=data["names"][i] + "-assoc={}".format(assoc),
                        x=data["perc_arrs"][i],  y=data["amat_values"][i],
                        text=data["mem_sizes"][i],
                        legendgroup=assoc,
                        showlegend=True if subplot_count == 0 else False,
                        line=dict(color=DEFAULT_PLOTLY_COLORS[assoc_index]),
                        marker=dict(symbol=i, size=10),
                        hovertext=data["miss_infos"][i],
                        hovertemplate=hovertemplate,
                        ), 
                        col = col, row = row)

                subplot_count += 1
        assoc_index += 1

    # To generate HTML output:
    file = filename
    pio.write_html(fig, file=file + ".html",
                        auto_open=False, include_plotlyjs="cdn")
    
    fig.write_image(file + ".pdf")
    fig.write_image(file + ".png")
    logging.info("Plot generated at: {}".format(file))



def plot_4k_paper(filename, data):

    def app_filter(app, method):
        if ((app == "redis" and method == "rand") or
            (app == "metis" and method == "linreg") or
            (app == "turi" and method == "graphcol")):
            return True
        else:
            return False

    assocs = []
    for (app, methods) in apps.items():
        for (method,props) in methods["methods"].items():
            if not app_filter(app, method):
                continue

            assocs = props['AMATs']['cachegrind']['pberry']['cache'].keys()

    output_file_data = {}

    for assoc in assocs:

        if assoc not in [4]:
            continue

        axis_title_font = dict(size=11, family='Calibri', color='black')
        axis_tick_font=dict(size=12, family='Calibri', color='black')
        legend_font=dict(size=11, family='Calibri', color='black')
        subplot_title_font=dict(size=12, family='Calibri', color='black')

        lines=['solid', 'dot', 'dash', '5px 10px 2px 2px', 'longdash', 'dashdot', 'solid']

        count = 0
        for (app, methods) in apps.items():
            for (method,props) in methods["methods"].items():

                if not app_filter(app, method):
                    continue

                fig = go.Figure()
                # fig.update_layout(font=subplot_title_font, 
                #                     title=dict( text=props['pretty_name'],
                #                                 xanchor='center', x=0.5))

                data = get_4k_single_figure_data (props, assoc, 1)
                output_file_data[props["pretty_name"]] = data

                for i in range(len(data["names"])):
                    fig.add_trace(go.Scatter(
                        name=data["names"][i], x=data["perc_arrs"][i],  y=data["amat_values"][i],
                        legendgroup="group",
                        showlegend=True if count == 2 else False,
                        line=dict(color=DEFAULT_PLOTLY_COLORS[i], width=1, dash=lines[i]),
                        marker=dict(symbol=i, size=5),
                        ))

                fig.update_xaxes(   showline=True, linewidth=1, linecolor='black',
                                    title_font=axis_title_font, tickfont=axis_tick_font,
                                    range=[0,115])

                fig.update_yaxes(   rangemode='tozero',
                                    showline=True, linewidth=1, linecolor='black',
                                    title_font=axis_title_font, tickfont=axis_tick_font)

            fig.update_xaxes(title_text="Cache Size (% Local Memory)")
            fig.update_yaxes(title_text="AMAT (ns)")

            fig.update_layout(
                plot_bgcolor='white',
                width=200, height=170,

                # margin=dict(t=30, b=0, l=0, r=10),
                margin=dict(t=0, b=0, l=0, r=10),

                # Legend settings
                legend=dict(font=legend_font, orientation="v", traceorder='normal',
                            bordercolor="Black", borderwidth=0,
                            y=0.9, x=1,
                            xanchor='right', yanchor="top")
                )

            # To generate HTML output:
            file = filename + "-" + app
            pio.write_html(fig, file=file + ".html",
                                auto_open=False, include_plotlyjs="cdn")
            
            fig.write_image(file + ".pdf")
            fig.write_image(file + ".png")
            logging.info("Plot generated at: {}".format(file))

            count += 1

    
    for app, data in output_file_data.items():
        del data["mem_sizes"]
        del data["miss_infos"]

    # logging.info("data={}".format(pformat(output_file_data)))
    json_file = filename + ".json"
    with open(json_file, 'w') as fp:
        json.dump(output_file_data, fp)

    counter = 1
    for app, data in output_file_data.items():
        csv_data = []
        csv_data.append(data["perc_arrs"][0])
        for amats in data["amat_values"]:
            csv_data.append(amats)

        transpose = list(map(list, zip(*csv_data)))
        header = data["names"]
        header.insert(0, "perc rss")
        transpose.insert(0, header)

        csv_file = filename + str(counter) + ".csv"
        with open(csv_file,"w+") as my_csv:
            csvWriter = csv.writer(my_csv,delimiter=',')
            csvWriter.writerows(transpose)

        counter += 1
