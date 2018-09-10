#!/usr/bin/env python3

import os
import pandas
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class PlotObject(object):
    def __init__(self, x, y, label='', style='b-', type='line'):
        self.x = x
        self.y = y
        self.label = label
        self.style = style
        self.type = type


def load_data(workingdir):

    # load the activity data
    path = os.path.join(workingdir, 'users.pkl')
    df = pandas.read_pickle(path)

    # convert dates
    df['date'] = pandas.to_datetime(df.usr_created_date).dt.normalize()
    df.usr_created_date = pandas.to_datetime(df.usr_created_date) \
                                .dt.normalize()
    df.usr_last_login_date = pandas.to_datetime(df.usr_last_login_date) \
                                   .dt.normalize()
    df.report_date = pandas.to_datetime(df.report_date).dt.normalize()

    # fill NA values.  This happens when a user never logs in
    df.usr_last_login_date = df.usr_last_login_date.fillna(0)

    # replace NaN to clean xls output
    df = df.fillna('')

    # add another date column and make it the index
    df['Date'] = df['date']

    # change the index to timestamp
    df.set_index(['Date'], inplace=True)

    return df


def subset_by_date(dat, st, et):

    if type(dat) == pandas.DataFrame:

        # select dates between start/end range
        mask = (dat.date >= st) & (dat.date < et)
        dat = dat.loc[mask]
        return dat

    elif type(dat) == pandas.Series:

        # select dates between start/end range
        mask = (dat.index >= st) & (dat.index < et)
        return dat.loc[mask]


def validate_inputs(working_dir, st, et):

    ######### check date formats #########
    try:
        st = datetime.strptime(st, '%m-%d-%Y')
    except ValueError:
        st = datetime.strptime('01-01-2000', '%m-%d-%Y')
        print('\tincorrect start date format, using default start date: 01-01-2000')
    try:
        et = datetime.strptime(et, '%m-%d-%Y')
    except ValueError:
        et = datetime.now()
        print('\tincorrect end date format, using default start date: %s' % et.strftime('%m-%d-%Y'))


    ######### check that dat exist #########
    if not os.path.exists(os.path.join(working_dir, 'activity.pkl')):
        print('\n\tcould not find \'activity.pkl\', skipping.'
              '\n\trun \'collect_hs_data\' to retrieve these missing data')

    return st, et


def plot(plotObjs_ax1, filename, plotObjs_ax2=[], *args, **kwargs):
    """
    Creates a figure give plot objects
    plotObjs: list of plot object instances
    filename: output name for figure *.png
    **kwargs: matplotlib plt args, e.g. xlabel, ylabel, title, etc
    """

    # create figure of these data
    print('--> making figure...')
    fig = plt.figure(figsize=(12, 9))
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.25)
    ax = plt.axes()

    # set plot attributes
    for k, v in kwargs.items():
        getattr(ax, 'set_'+k)(v)

    for pobj in plotObjs_ax1:
        if pobj.type == 'line':
            ax.plot(pobj.x, pobj.y, pobj.style, label=pobj.label)
        elif pobj.type == 'bar':
            ax.bar(pobj.x, pobj.y, 10, label=pobj.label)

    if len(plotObjs_ax2) > 0:
        ax2 = ax.twinx()
        for pobj in plotObjs_ax2:
            if pobj.type == 'line':
                ax2.plot(pobj.x, pobj.y, pobj.style, label=pobj.label)
            elif pobj.type == 'bar':
                ax2.bar(pobj.x, pobj.y, 10, label=pobj.label)

    # add a legend
    plt.legend()

    # add monthly minor ticks
    months = mdates.MonthLocator()
    ax.xaxis.set_minor_locator(months)

    # save the figure and the data
    print('--> saving figure as %s' % filename)
    plt.savefig(filename)


def distinct_organizations(workingdir, st, et, label=''):

    print('--> calculating distinct organizations')

    # load the data based on working directory and subset it if necessary
    df = load_data(workingdir)
    df = subset_by_date(df, st, et)

    # group and cumsum
    df = df.sort_index()
    grp = '1M'
    ds = df.groupby(pandas.TimeGrouper(grp)).usr_organization.nunique()

    # create plot object
    x = ds.index
    y = ds.values.tolist()
    plot = PlotObject(x, y, label=label, type='bar')

    return [plot]


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='hydroshare organization'
                                                 ' statistics')
    parser.add_argument('--working-dir',
                        help='path to directory containing elasticsearch data',
                        required=True)
    parser.add_argument('--st',
                        help='reporting start date MM-DD-YYYY',
                        default='01-01-2000')
    parser.add_argument('--et',
                        help='reporting end date MM-DD-YYYY',
                        default=datetime.now().strftime('%m-%d-%Y'))
    parser.add_argument('-d',
                        help='plot distinct organization',
                        action='store_true')
    args = parser.parse_args()

    st, et = validate_inputs(args.working_dir, args.st, args.et)

    if args.d:
        plots = distinct_organizations(args.working_dir, st, et)
        plot(plots, os.path.join(args.working_dir,
                                 'hydroshare_distinct_organizations.png'),
             title='Distinct User Organizations',
             ylabel='Number of Organizations',
             xlabel='User Account Creation Date')




