#!/usr/bin/env python3 

import os
import pytz
import numpy
import pandas
import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pyplot import cm

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


class PlotObject(object):
    def __init__(self, x, y, label='', color='b', linestyle='-'):
        self.x = x
        self.y = y
        self.label = label
        self.linestyle = linestyle
        self.color = color


def line(plotObjs_ax1,
         filename,
         plotObjs_ax2=[],
         axis_dict={},
         figure_dict={},
         rcParams={},
         **kwargs):
    """
    Creates a figure give plot objects
    plotObjs: list of plot object instances
    filename: output name for figure *.png
    **kwargs: matplotlib plt args, e.g. xlabel, ylabel, title, etc
    """

    print('--> making figure...')

    # set global plot attributes
    if rcParams != {}:
        plt.rcParams.update(rcParams)

    # create figure of these data
    fig, ax = plt.subplots()
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.25)

    for pobj in plotObjs_ax1:
        ax.plot(pobj.x, pobj.y,
                color=pobj.color,
                linestyle=pobj.linestyle,
                label=pobj.label)
        # annotate the last point
        ax.text(pobj.x[-1] + timedelta(days=5), # x-loc
                pobj.y[-1], # y-loc
                pobj.y[-1], # text value
                bbox=dict(boxstyle='square,pad=0.5',
                          fc='none', # foreground color
                          ec='none', # edge color
                          ))

    ax.grid()

    if len(plotObjs_ax2) > 0:
        ax2 = ax.twinx()
        for pobj in plotObjs_ax2:
            ax2.plot(pobj.x, pobj.y,
                     color=pobj.color,
                     linestyle=pobj.style,
                     label=pobj.label)

    # add a legend
    plt.legend()

    # add monthly minor ticks
    months = mdates.MonthLocator()
    ax.xaxis.set_minor_locator(months)
    
    # set plot attributes
    for k, v in axis_dict.items():
        # eval if string is a tuple
        if '(' in v:
            v = eval(v)
        getattr(ax, 'set_'+k)(v)
    
    for k, v in figure_dict.items():
        getattr(plt, k)(v)


#    for k, v in text_dict.items():
#        getattr(ax, k)(v)

    # save the figure and the data
    print('--> saving figure as %s' % filename)
    plt.savefig(filename)




