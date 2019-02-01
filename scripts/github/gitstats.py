#!/usr/bin/env python3

import os

import pandas
from tabulate import tabulate

import collectdata
import plot
import tabular

from datetime import datetime


def run_statistics(csv, dirname):

    # load the csv file into a pandas dataframe
    df = pandas.read_csv(csv, sep=',', comment='#')
    df['created_dt'] = pandas.to_datetime(df.created_dt, errors='coerce') \
                             .dt.normalize()
    df['closed_dt'] = pandas.to_datetime(df.closed_dt, errors='coerce') \
                            .dt.normalize()

    # summarize all issues by label
    d = df.groupby('label').count().number.to_frame()
    d.columns = ['all_issues']

    # summarize all open issues
    d1 = df[df.state == 'open'].groupby('label').count().number.to_frame()
    d1.columns = ['open_issues']

    d = d.merge(d1, left_index=True, right_index=True)
    tbl = tabulate(d.sort_values('all_issues', ascending=False),
                   headers='keys', tablefmt='psql')
    print(tbl)

    # indicate issues as either 'open' or 'closed'
    df.loc[df.state == 'open', 'open'] = 1
    df.loc[df.state == 'closed', 'closed'] = 1

    # make plots
    plot.open_issues(df, dirname)
    plot.all_issues(df, dirname)

    st = datetime(2018, 9, 1)
    et = datetime(2018, 12, 1)
    tabular.all_resolved_issues(df, st, et, dirname)
    tabular.resolved_bugs(df, st, et, dirname)
    tabular.resolved_features(df, st, et, dirname)


def get_working_directory():

    # create a directory for these data
    dirname = datetime.now().strftime('%m.%d.%Y')

    if os.path.exists(dirname):
        return dirname
    else:
        os.makedirs(dirname)

    print('Metrics will be saved into: %s' % dirname)

    return dirname


if __name__ == "__main__":

    dirname = get_working_directory()
    csv = os.path.join(dirname, 'hydroshare_git_issues.csv')

    if not os.path.exists(os.path.join(csv)):
        print('\nCould not find %s, proceeding to download git '
              'tickets.\n' % csv)

        # collect data
        url = "https://api.github.com/repos/hydroshare/hydroshare/issues"
        collectdata.get_data(url, csv)
    else:
        print('\nFound %s, proceeding to re-use. ' % csv)
        print('If this is not the desired functionality, '
              'remove %s and re-run.\n' % csv)

    # run the statistics routine to generate plots
    run_statistics(csv, dirname)

