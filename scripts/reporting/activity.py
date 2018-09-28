#!/usr/bin/env python3

import os
import pandas
import argparse
import numpy as np
from tabulate import tabulate
from datetime import datetime


def load_data(workingdir, pickle_file='activity.pkl'):

    # load the activity data
    path = os.path.join(workingdir, pickle_file)
    df = pandas.read_pickle(path)

    # convert dates
    df['date'] = pandas.to_datetime(df.session_timestamp) \
                       .dt.normalize()

    # add another date column and make it the index
    df['Date'] = df['date']

    # change the index to timestamp
    df.set_index(['Date'], inplace=True)

    return df


def subset_by_date(dat, st, et):

    if type(dat) == pandas.DataFrame:

        # select dates between start/end range
        mask = (dat.date >= st) & (dat.date <= et)
        dat = dat.loc[mask]
        return dat

    elif type(dat) == pandas.Series:

        # select dates between start/end range
        mask = (dat.index >= st) & (dat.index <= et)
        return dat.loc[mask]


def activity_table(working_dir, st, et, agg='Q'):

    print('--> calculating activity')

    # load the data based on working directory
    df = load_data(working_dir, 'activity.pkl')
    df = df.filter(['action'], axis=1)

    # create columns for each action
    for act in df.action.unique():
        df[act] = np.where(df.action == act, 1, 0)

    # remove the action column since its been divided into 
    # individual columns
    df.drop('action', inplace=True)

    df = df.groupby(pandas.Grouper(freq=agg)).sum()

    print(tabulate(df, headers='keys', tablefmt='psql'))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--working-dir',
                        help='path to directory containing elasticsearch data',
                        required=True)
    parser.add_argument('--agg',
                        help='aggregation, i.e http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases.',
                        default='1D')
    parser.add_argument('--active-range',
                        help='number of days that qualify a user as active',
                        default=90)
    parser.add_argument('--figure-title',
                        help='title for the output figure',
                        default='HydroShare User Summary %s'
                        % datetime.now().strftime('%m-%d-%Y'))
    parser.add_argument('--filename',
                        help='filename for the output figure',
                        default='hydroshare-users.png')
    parser.add_argument('--st',
                        help='start time MM-DD-YYYY',
                        default='01-01-2000')
    parser.add_argument('--et',
                        help='start time MM-DD-YYYY',
                        default=datetime.now().strftime('%m-%d-%Y'))
    parser.add_argument('-t',
                        help='create activity table',
                        action='store_true')
    args = parser.parse_args()

    # check date formats 
    st_str = args.st
    et_str = args.et
    try:
        st = datetime.strptime(st_str, '%m-%d-%Y')
    except ValueError:
        st = datetime.strptime('01-01-2000', '%m-%d-%Y')
        print('\tincorrect start date format, using default start '
              'date: 01-01-2000')
    try:
        et = datetime.strptime(et_str, '%m-%d-%Y')
    except ValueError:
        et = datetime.now()
        print('\tincorrect end date format, using default start date: %s'
              % et.strftime('%m-%d-%Y'))

    # check that dat exist
    if not os.path.exists(os.path.join(args.working_dir, 'activity.pkl')):
        print('\n\tcould not find \'activity.pkl\', skipping.'
              '\n\trun \'collect_hs_data\' to retrieve these missing data')
    else:
        # cast input strings to integers
        agg = args.agg
        activedays = int(args.active_range)

        if args.t:
            res = activity_table(args.working_dir, st, et, agg)
