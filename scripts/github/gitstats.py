#!/usr/bin/env python3

import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import pandas
from tabulate import tabulate
import numpy as np
from datetime import datetime, timedelta

import collectdata


def run_statistics(csv):

    # load the csv file into a pandas dataframe
    df = pandas.read_csv(csv, sep=',', comment='#')
    df['created_dt'] = pandas.to_datetime(df.created_dt, errors='coerce').dt.normalize()
    df['closed_dt'] = pandas.to_datetime(df.closed_dt, errors='coerce').dt.normalize()

    # summarize all issues by label
    d = df.groupby('label').count().number.to_frame()
    d.columns = ['all_issues']
    # summarize all open issues
    d1 = df[df.state == 'open'].groupby('label').count().number.to_frame()
    d1.columns = ['open_issues']
    d = d.merge(d1, on='label')
    tbl = tabulate(d.sort_values('all_issues', ascending=False),
                   headers='keys', tablefmt='psql')
    print(tbl)

    # indicate issues as either 'open' or 'closed'
    df.loc[df.state == 'open', 'open'] = 1
    df.loc[df.state == 'closed', 'closed'] = 1

    # select unique issue numbers to remove duplicates caused by
    # issues having multiple labels
    df_unique = df.drop_duplicates('number')

    # group by date
    df_dt = df_unique.groupby(pandas.Grouper(key='created_dt', freq='W')).count().cumsum()

    # create a figure to summarize technical debt
    fig = plt.figure()
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.15)
    plt.ylabel('issue count')
    plt.xlabel('date')
    plt.title('HydroShare Issue Status')
    ax = plt.gca()

    xdata = df_dt.index
    xfloat = np.array([(i - datetime(1970, 1, 1)) / timedelta(seconds=1) for i in xdata]).astype('float')

    ydata = df_dt.number.values
    plt.plot(xdata, df_dt.number, color='k', linestyle='-', label='all')

    ydata = df_dt.closed.values
    plt.plot(xdata, ydata, color='b', linestyle='-', label='closed')

    ydata = df_dt.open.values
    plt.plot(xdata, df_dt.open, color='r', linestyle='-', label='open')
    plt.legend()
    plt.tight_layout()
    plt.savefig('hs-issue-status.png')

    # plot a summary of open issues
    df_open = df[df.state == 'open']

    # group open bugs by date
    df_open_bug = df_open[df_open.label == 'bug']
    df_open_bug_list = list(df_open_bug.number.values)
    df_open_bug = df_open_bug.groupby(pandas.Grouper(key='created_dt', freq='W')).count().cumsum()

    # group open enhancements by date
    df_open_enh = df_open[df_open.label == 'enhancement']
    df_open_enh_list = list(df_open_enh.number.values)
    df_open_enh = df_open_enh.groupby(pandas.Grouper(key='created_dt', freq='W')).count().cumsum()

    # group all open issues that are not bugs or enhancements by date
    df_open_non = df_open[~df_open.label.isin(['bug', 'enhancement'])]
    df_open_non = df_open_non.drop_duplicates('number')

    # remove all issue numbers that exist in enhancements and bugs lists
    bug_enh_tickets = list(df_open_bug_list) + list(df_open_enh_list)
    df_open_non = df_open_non[~df_open_non.isin(bug_enh_tickets)]

    df_open_non = df_open_non.groupby(pandas.Grouper(key='created_dt', freq='W')).count().cumsum()
    print('%d non-bug, non-enhancement issues' % (len(df_open_non.number)))

    fig = plt.figure()
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.15)
    plt.ylabel('issue count')
    plt.xlabel('date')
    plt.title('HydroShare Open Issues Summary')
    ax = plt.gca()

    xdata = df_open_non.index
    ydata = df_open_non.number.values
    print(ydata[-1])
    plt.plot(xdata, ydata, color='k', linestyle='-', label='non-bug, non-enhancement')

    xdata = df_open_bug.index
    ydata = df_open_bug.number.values
    plt.plot(xdata, ydata, color='r', linestyle='-', label='bugs')

    xdata = df_open_enh.index
    ydata = df_open_enh.number.values
    plt.plot(xdata, ydata, color='b', linestyle='-', label='enhancements')

    plt.legend()
    plt.tight_layout()
    plt.savefig('hs-open-issues-summary.png')


if __name__ == "__main__":

    csv = 'hydroshare_git_issues.csv'

    if not os.path.exists(csv):
        print('\nCould not find %s, proceeding to download git tickets.\n' % csv)
        url = "https://api.github.com/repos/hydroshare/hydroshare/issues"
        outpath = 'hydroshare_git_issues.csv'
        collectdata.get_data(url, outpath)
    else:
        print('\nFound %s, proceeding to re-use. ' % csv)
        print('If this is not the desired functionality, '
              'remove %s and re-run.\n' % csv)

    run_statistics(csv)

