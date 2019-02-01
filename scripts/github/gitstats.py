#!/usr/bin/env python3

import os

import pandas
from tabulate import tabulate

import collectdata
import plot
import tabular

from datetime import datetime


def run_statistics(csv):

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

#    # make plots
#    plot.open_issues(df)
#    plot.all_issues(df)

    st = datetime(2018, 9, 1)
    et = datetime(2018, 12, 1)
    tabular.all_resolved_issues(df, st, et)
    tabular.resolved_bugs(df, st, et)
    tabular.resolved_features(df, st, et)


if __name__ == "__main__":

    csv = 'hydroshare_git_issues.csv'

    if not os.path.exists(csv):
        print('\nCould not find %s, proceeding to download git '
              'tickets.\n' % csv)

        # collect data
        url = "https://api.github.com/repos/hydroshare/hydroshare/issues"
        outpath = 'hydroshare_git_issues.csv'
        collectdata.get_data(url, outpath)
    else:
        print('\nFound %s, proceeding to re-use. ' % csv)
        print('If this is not the desired functionality, '
              'remove %s and re-run.\n' % csv)

    # run the statistics routine to generate plots
    run_statistics(csv)

