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
    def __init__(self, x, y,
                 dataframe=None,
                 label='',
                 color='b',
                 linestyle='-'):
        self.x = x
        self.y = y
        self.label = label
        self.linestyle = linestyle
        self.color = color
        self.dataframe = dataframe

    @property
    def df(self):
        if self.dataframe is None:
            _df = pandas.DataFrame(self.y, index=self.x, columns=[self.label])
            _df.index = pandas.to_datetime(_df.index)
            return _df
        return self.dataframe


def line(plotObjs_ax1,
         filename,
#         plotObjs_ax2=[],
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

    annotate = figure_dict.pop('annotate', False)
    for pobj in plotObjs_ax1:
        ax.plot(pobj.x, pobj.y,
                color=pobj.color,
                linestyle=pobj.linestyle,
                label=pobj.label)

        # annotate the last point
        if annotate:
            ax.text(pobj.x[-1] + timedelta(days=5), # x-loc
                    pobj.y[-1], # y-loc
                    int(round(pobj.y[-1], 0)), # text value
                    bbox=dict(boxstyle='square,pad=0.5',
                              fc='none', # foreground color
                              ec='none', # edge color
                              ))
    # turn on the grid
    if figure_dict.pop('grid', False):
        ax.grid()

    # add a legend
    if figure_dict.pop('legend', False):
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
    plt.savefig(filename)
    print(f'--> figure saved to: {filename}')



def bar(plotObjs_ax1,
        filename,
        width=10,
        axis_dict={},
        figure_dict={},
        rcParams={},
        **kwargs):

#        title='',
#              agg='1M', width=.5, annotate=False,
#              **kwargs):

    print('--> making figure...')
    
    # set global plot attributes
    if rcParams != {}:
        plt.rcParams.update(rcParams)

    # create figure of these data
    fig, ax = plt.subplots()
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.25)

    annotate = figure_dict.pop('annotate', False)
    for pobj in plotObjs_ax1:
        ax.bar(pobj.x, 
               pobj.y,
               width=float(width),
               color=pobj.color)

        if annotate:
            for p in ax.patches:
                height = p.get_height()
                if height > 0:
                    ax.annotate("%d" % height,
                                (p.get_x() + p.get_width() / 2.,
                                 height),
                                ha='center',
                                va='center',
                                xytext=(0, 10),
                                textcoords='offset points')

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

    # save the figure and the data
    plt.savefig(filename)
    print(f'--> figure saved to: {filename}')


def pie(plotObjs_ax1,
        filename,
        axis_dict={},
        figure_dict={},
        rcParams={},
        **kwargs):

    print('--> making figure...')

    # set global plot attributes
    if rcParams != {}:
        plt.rcParams.update(rcParams)

    # create figure of these data
    fig, ax = plt.subplots()

    for pobj in plotObjs_ax1:
        pobj.df[pobj.label].plot.pie(ax=ax,
                                     labeldistance=1.1)

    plt.tight_layout()

    # set plot attributes
    for k, v in axis_dict.items():
        # eval if string is a tuple
        if '(' in v:
            v = eval(v)
        getattr(ax, 'set_'+k)(v)

    for k, v in figure_dict.items():
        getattr(plt, k)(v)

    # save the figure and the data
    plt.savefig(filename)
    print(f'--> figure saved to: {filename}')
