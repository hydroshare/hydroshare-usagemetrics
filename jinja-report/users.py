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


def load_data(workingdir, pickle_file='users.pkl'):

    # load the activity data
    path = os.path.join(workingdir, pickle_file)
    df = pandas.read_pickle(path)

    columns = df.columns

    # parse users
    if 'usr_created_date' in columns:

        # convert dates
        df['date'] = pandas.to_datetime(df.usr_created_date).dt.normalize()

        df.usr_created_date = pandas.to_datetime(df.usr_created_date) \
                                    .dt.normalize()
        df.usr_last_login_date = pandas.to_datetime(df.usr_last_login_date) \
                                       .dt.normalize()
        df.report_date = pandas.to_datetime(df.report_date) \
                               .dt.normalize()

#        # fill NA values.  This happens when a user never logs in
#        df.usr_last_login_date = df.usr_last_login_date.fillna(0, downcast=False)

#        # replace NaN to clean xls output
#        df = df.fillna('', downcast=False)

        # add another date column and make it the index
        df['Date'] = df['date']

        # change the index to timestamp
        df.set_index(['Date'], inplace=True)

    # parse activity
    elif 'session_timestamp' in columns:

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


def total(input_directory='.',
          start_time=datetime(2000, 1, 1),
          end_time=datetime(2030, 1, 1),
          step=1,
          label='total users',
          color='k',
          linestyle='-',
          **kwargs):

    print('--> calculating total users')

    # load the data based on working directory
    df = load_data(input_directory)

    # group and cumsum
    df = df.sort_index()
    grp = '%dd' % step
    ds = df.groupby(pandas.Grouper(freq=grp)).count().usr_id.cumsum()

    ds = subset_by_date(ds, start_time, end_time)

    # create plot object
    x = ds.index
    y = ds.values.tolist()
    plot = PlotObject(x, y, label=label, color=color, linestyle=linestyle)

    return plot


def active(input_directory='',
           start_time=datetime(2000, 1, 1),
           end_time=datetime(2000, 1, 1),
           active_range=30,
           step=1,
           label='Active Users',
           color='b',
           linestyle='-',
           **kwargs):
    """
    Calculates the number of active users for any given time frame.
    An active user is a user that has performed a HydroShare action 
    (as defined in activity.pkl) within the specified active range.
    """

    print('--> calculating active users')

    # load the data based on working directory
    df = load_data(input_directory, 'activity.pkl')
    df = subset_by_date(df, start_time, end_time)
    df = df.sort_index()

    dfu = load_data(input_directory, 'users.pkl')
    dfu = subset_by_date(dfu, start_time, end_time)

    x, y = [], []

    # set the start date as the earliest available date plus the 
    # active date range
    t = df.date.min() + timedelta(days=active_range)
    while t < end_time:

        min_active_date = t - timedelta(days=active_range)

        # isolate users that performed an action
        subdf = df[(df.date <= t) &
                   (df.date > min_active_date)]
        total_active_users = subdf.user_id.nunique()

        # save the results
        x.append(t)
        y.append(total_active_users)

        t += timedelta(days=step)

    # create plot object
    plot = PlotObject(x, y, label=label,
                      color=color, linestyle=linestyle)

    with open(f'{input_directory}/active-users-{active_range}.csv', 'w') as f:
        f.write(f'Date,Number of Active Users (logged in with {active_range} days)\n')
        for i in range(0, len(x)):
            f.write(f'{str(x[i])},{y[i]}\n')

    return plot


def new(input_directory='.',
        start_time=datetime(2000, 1, 1),
        end_time=datetime(2030, 1, 1),
        active_range=30,
        step=1,
        label='New Users',
        color='g',
        linestyle='-',
        **kwargs):

    # load the data based on working directory
    df = load_data(input_directory)
    df = subset_by_date(df, start_time, end_time)

    print('--> calculating new users')
    x = []
    y = []

    t = df['usr_created_date'].min()
    while t < end_time:

        earliest_date = t - timedelta(days=active_range)

        subdfn = df[(df.usr_created_date <= t) &
                    (df.usr_created_date > earliest_date)]
        new = subdfn.usr_id.nunique()

        y.append(new)
        x.append(t)

        t += timedelta(days=step)

    # create plot object
    plot = PlotObject(x, y, label=label, color=color, linestyle=linestyle)

    return plot


def returning(input_directory='.',
              start_time=datetime(2000, 1, 1),
              end_time=datetime(2030, 1, 1),
              active_range=30,
              step=10,
              color='r',
              label='Returning Users',
              linestyle='-',
              **kwargs):

    # load the data based on working directory
    df = load_data(input_directory, 'users.pkl')
    df = subset_by_date(df, start_time, end_time)
    dfa = load_data(input_directory, 'activity.pkl')
    dfa = subset_by_date(dfa, start_time, end_time)

    print('--> calculating returning users')
    x = []
    y = []

    # set the start date as the earliest available date plus the 
    # active date range
    t = dfa.date.min() + timedelta(days=active_range)
#    n = []
#    a = []
    while t < end_time:
        earliest_date = t - timedelta(days=active_range)

        ## subset all users to those that exist up to the current time, t
        #subdf = df[df.usr_created_date <= t]

        subdfn = df[(df.usr_created_date <= t) &
                    (df.usr_created_date > earliest_date)]
        new = subdfn.usr_id.nunique()

        # calculate active users for this range
        subdfa = dfa[(dfa.date <= t) &
                     (dfa.date > earliest_date)]
        active = subdfa.user_id.nunique()

        # Users who were active, but obtained an account prior to the
        # active period are users who continue to return to and work
        # with HydroShare.
        y.append(active - new)
        x.append(t)

        t += timedelta(days=step)

    # create plot object
    plot = PlotObject(x, y, label=label, color=color, linestyle=linestyle)
    return plot


def users_by_type(working_dir, st, et, utypes='University Faculty', agg='1D'):

    # load the data based on working directory
    df = load_data(working_dir, 'users.pkl')
    df = subset_by_date(df, st, et)

    # define HS user types
    usertypes = ['Unspecified', 'Post-Doctoral Fellow',
                 'Commercial/Professional', 'University Faculty',
                 'Government Official', 'University Graduate Student',
                 'Professional', 'University Professional or Research Staff',
                 'Local Government', 'University Undergraduate Student',
                 'School Student Kindergarten to 12th Grade',
                 'School Teacher Kindergarten to 12th Grade', 'Other']

    # clean the data
    df.loc[~df.usr_type.isin(usertypes), 'usr_type'] = 'Other'

    # loop through each of the user types
    plots = []
    colors = iter(cm.jet(numpy.linspace(0, 1, len(utypes))))
    for utype in utypes:

        # group by user type
        du = df.loc[df.usr_type == utype]

        # remove null values
        du = du.dropna()

        # group by date frequency
        ds = du.groupby(pandas.Grouper(freq=agg)).count().usr_type.cumsum()
        x = ds.index.values
        y = ds.values
        c = next(colors)

        # create plot object
        plot = PlotObject(x, y, label=utype, color=c, linestyle='-')

        plots.append(plot)

    return plots


def plot(plotObjs_ax1,
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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='general user statistics')
    parser.add_argument('--working-dir',
                        help='path to directory containing elasticsearch data',
                        required=True)
    parser.add_argument('--step',
                        help='timestep to use in aggregation in days',
                        default=10)
    parser.add_argument('--active-range',
                        help='number of days that qualify a user as active',
                        default=90)
    parser.add_argument('--figure-title',
                        help='title for the output figure',
                        default='HydroShare User Summary %s' \
                        % datetime.now().strftime('%m-%d-%Y') )
    parser.add_argument('--filename',
                        help='filename for the output figure',
                        default='hydroshare-users.png')
    parser.add_argument('--st',
                        help='start time MM-DD-YYYY (UTC)',
                        default='01-01-2000')
    parser.add_argument('--et',
                        help='start time MM-DD-YYYY (UTC)',
                        default=datetime.now().strftime('%m-%d-%Y'))
    parser.add_argument('-t',
                        help='plot total users line',
                        action='store_true')
    parser.add_argument('-a',
                        help='plot active users line',
                        action='store_true')
    parser.add_argument('-n',
                        help='plot new users line',
                        action='store_true')
    parser.add_argument('-r',
                        help='plot returning users line',
                        action='store_true')
    parser.add_argument('-u',
                        help='plot user types',
                        action='store_true')
    parser.add_argument('--utypes',
                        nargs='+',
                        help='user types to plot. use this arg with "-u"',
                        default=[])
    parser.add_argument('--agg',
                        help='aggregation to use, e.g. 1W. use this arg with "-u"',
                        default='1W')

    args = parser.parse_args()

    ######### check date formats #########
    st_str = args.st
    et_str = args.et
    try:
        st = datetime.strptime(st_str, '%m-%d-%Y')
    except ValueError:
        st = datetime.strptime('01-01-2000', '%m-%d-%Y')
        print('\tincorrect start date format, using default start date: 01-01-2000')
    try:
        et = datetime.strptime(et_str, '%m-%d-%Y')
    except ValueError:
        et = datetime.now()
        print('\tincorrect end date format, using default start date: %s' % et.strftime('%m-%d-%Y'))

    # set timezone to UTC
    st = pytz.utc.localize(st)
    et = pytz.utc.localize(et)

    print(args.working_dir)
    # check that dat exist
    if not os.path.exists(os.path.join(args.working_dir, 'activity.pkl')):
        print('\n\tcould not find \'activity.pkl\', skipping.'
              '\n\trun \'collect_hs_data\' to retrieve these missing data')
    else:
        # cast input strings to integers
        step = int(args.step)
        activedays = int(args.active_range)

        plots = []
        if args.t:
            res = total(args.working_dir, st, et,
                        step)
            plots.append(res)
        if args.a:
            res = active(args.working_dir, st, et,
                         activedays, step)
            plots.append(res)
        if args.n:
            res = new(args.working_dir, st, et,
                      activedays, step)
            plots.append(res)
        if args.r:
            res = returning(args.working_dir, st, et,
                            activedays, step)
            plots.append(res)
        if args.u:
            res = users_by_type(args.working_dir, st, et,
                                utypes=args.utypes,
                                agg=args.agg)
            plots.extend(res)
        if len(plots) > 0:
            plot(plots, args.filename,
                 title=args.figure_title,
                 ylabel='Number of Users',
                 xlabel='Date')



