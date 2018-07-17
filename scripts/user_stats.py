#!/usr/bin/env python3 

import os
import csv
import pandas
import numpy as np
from tabulate import tabulate
from datetime import datetime, timedelta
from workbook import workbook
from collections import OrderedDict
import matplotlib.pyplot as plt


class Users(object):

    def __init__(self, workingdir, outxls, st, et):

        self.workingdir = workingdir
        self.outxls = outxls
        self.st = st
        self.et = et
        self.df = self.load_data()

    def load_data(self):

        print('--> reading user statistics...', end='', flush=True)
        # load the activity data
        path = os.path.join(self.workingdir, 'users.pkl')
        df = pandas.read_pickle(path)

        # convert dates
        df['date'] = pandas.to_datetime(df.usr_created_date).dt.normalize()
        df.usr_created_date = pandas.to_datetime(df.usr_created_date).dt.normalize()
        df.usr_last_login_date = pandas.to_datetime(df.usr_last_login_date).dt.normalize()
        df.report_date = pandas.to_datetime(df.report_date).dt.normalize()
        # fill NA values.  This happens when a user never logs in
        df.usr_last_login_date = df.usr_last_login_date.fillna(0)

        # replace NaN to clean xls output
        df = df.fillna('')

        # change the index to timestamp
        df.set_index(['date'], inplace=True)

        print('done', flush=True)

        return df

    def users_over_time(self):
        """
        Calculate total users over time
        """
        output = OrderedDict()
        df = self.df.sort_index()


        print('--> calculating rolling statistics... ', end='', flush=True)
        res = []
        t = df['usr_created_date'].min()

        activerange = 90
        output['dates'] = []
        output['total-users'] = []
        output['active-users'] = []
        output['new-users'] = []
        output['returning-users'] = []

        while t < self.et:

            output['dates'].append(t)

            # subset all users to those that exist up to the current time, t
            subdf = df[df.usr_created_date <= t]

            # total users up to time, t
            output['total-users'].append(subdf.usr_created_date.count())

            # The number of new users in activerange up to time dateJoined[i] (i.e. the range 1:i) are users who 
            # created their account after dateJoine[i]-activerange
            earliest_date = t - timedelta(days=activerange)
            output['new-users'].append(np.where((subdf.usr_created_date >= earliest_date) &
                                                (subdf.usr_created_date <= t),
                                                1, 0).sum())

            account_age = (t - subdf.usr_created_date).astype('timedelta64[D]')
#            output['new-users'].append(np.where((account_age <= activerange) &
#                                                (account_age >= 0),
#                                                1, 0).sum())

            # The number of users active at time dateJoined[i] is all who created an account before dateJoined[i]
            # i.e. the range 1:i, who have logged in after dateJoine[i]-activerange
            output['active-users'].append((subdf.usr_last_login_date > (t - timedelta(days=activerange))).sum())
#            days_since_login = (t - subdf.usr_last_login_date).astype('timedelta64[D]')


            # Users who were active on the site in the last 90 days,
            # but obtained an account prior to the last 90 days are people who
            # continue to return to and work with HydroShare.
            output['returning-users'].append(output['active-users'][-1] - output['new-users'][-1])
#        output['returning-users'].append(np.where((days_since_login <= activerange) &
#                                                      (days_since_login >= 0) &
#                                                      (account_age > activerange),
#                                                      1, 0).sum())
            t += timedelta(days=1)

        opath = os.path.join(self.workingdir, 'user-stats.csv')
        with open(opath, 'w') as f:
            f.write('%s\n' % (','.join(list(output.keys()))))
            for i in range(0, len(output['dates'])):
                for k in output.keys():
                    f.write('%s,' % str(output[k][i]))
                f.write('\n')
        opath = os.path.join(self.workingdir, 'user-statistics.README')
        with open(opath, 'w') as f:
            f.write('The following assumptions are made when deriving '
                    'HS user statistics:\n\n'
                    '1. New users are those who created an account within the [active range] of the current date [t]. For example, NewUser = True if:\n  - ([t] - [active range]) <= [date joined] <= [t] \n\n'
                    '2. Active users are defined as those who created an account before time [t] and have logged into HS within the [active range] or have created a new account within the [active rage]. For example, ActiveUser = True if:\n  - ([date joined] < [t]) AND ([t] - [active range]) <= [last login] <= [t]\n  - OR ([t] - [active range]) <= [date joined] <= [t]\n')

        print('done', flush=True)

        print('--> creating user statistics figures... ', end='', flush=True)

        def makefig(title, xlabel, ylabel, dic, filename):
            fig = plt.figure()
            plt.xticks(rotation=45)
            plt.subplots_adjust(bottom=0.15)
            plt.ylabel(ylabel)
            plt.xlabel(xlabel)
            plt.title(title)

            xdata = output['dates']
            for s in dic:
                plt.plot(xdata, output[s[0]], color=s[1], linestyle=s[2],
                         label=s[3])
            plt.legend()
            plt.tight_layout()
            outpath = os.path.join(self.workingdir, filename)
            plt.savefig(outpath)

        series = [['total-users', 'k', '-', 'Total'],
                  ['active-users', 'b', '--', 'Active (last 90 days)'],
                  ['new-users', 'r', '--', 'New (last 90 days)']]

        makefig('HydroShare Users as of %s' % (self.et.strftime('%Y-%m-%d')),
                'Date',
                'Number of Users',
                series,
                '1-all-users-overview.png')

        series = [['active-users', 'k', '-', 'Active (last 90 days)'],
                  ['new-users', 'r', '--', 'New (last 90 days)'],
                  ['returning-users', 'b', '--', 'Returned (last 90 days)']]

        makefig('Active HydroShare Users as of %s' % (self.et.strftime('%Y-%m-%d')),
                'Date',
                'Number of Users',
                series,
                '2-active-users-overview.png')

        print('done', flush=True)


#        while t < self.et:
#            df['days-since-login'] = (t - df.usr_last_login_date).astype('timedelta64[D]')
#            df['account-age'] = (t - df.usr_created_date).astype('timedelta64[D]')
#            df['is-new-user'] = np.where((df['account-age'] <= 90) &
#                                         (df['account-age'] >= 0), 1, 0)
#            df['is-active'] = np.where(((df['days-since-login'] <= 90) &
#                                        (df['days-since-login'] >= 0)) ,
#                                            1, 0)
#            df['is-returning-user'] = np.where((df['is-new-user'] == 0) &
#                                               (df['days-since-login'] <= 90) &
#                                               (df['days-since-login'] >= 0),
#                                               1, 0)
#
#            # The number of users active at time dateJoined[i] is all who created an account before dateJoined[i]
#            # i.e. the range 1:i, who have logged in after dateJoine[i]-activerange
##            df['is-active'] = np.where(df.usr_last_login_date >
##                                       ((t - timedelta(days=90)) &
##                                        (df.usr_last_login_date <= t)),
##                                       1, 0)
#            # The number of new users in activerange up to time dateJoined[i] (i.e. the range 1:i) are users who 
#            # created their account after dateJoine[i]-activerange
#            df['is-new'] = np.where(df.usr_created_date > 
#                                    (t - timedelta(days=90)),
#                                    1, 0)
#
#            total_accounts = df[df['account-age'] >= 0]['account-age'].count()
##            total_new = df['is-new-user'].sum()
##            total_active = df['is-active-user'].sum()
#            total_active = df['is-active'].sum()
#            total_new = df['is-new'].sum()
##            total_returning = df['is-returning-user'].sum()
#            res.append([t, total_accounts, total_active, 
#                        total_new])#, total_returning])
#
##            import pdb; pdb.set_trace()
#            t += timedelta(days=1)
#        print('done', flush=True)
#
#        print('--> saving rolling statistics... ', end='', flush=True)
#        opath = os.path.join(self.workingdir, 'rolling-stats.csv')
#        with open(opath, 'w') as f:
#            f.write('date, total-accounts, total-active,'
#                    'total-new, total-returning\n')
#            for r in res:
#                f.write('%s, %s\n' % (r[0], ','.join(map(str, r[1:]))))
#        print('done', flush=True)
#
#        print('--> creating user statistics figure... ', end='', flush=True)
#        fig = plt.figure()
#        plt.xticks(rotation=45)
#        plt.subplots_adjust(bottom=0.15)
#        plt.ylabel('Number Users')
#        plt.xlabel('Date')
#        plt.title('HydroShare Users as of %s' % (self.et.strftime(
#                                                 '%Y-%m-%d')))
#        d = np.array(res)
#        plt.plot(d[:, 0], d[:, 1], color='k', linestyle='-',
#                 label='Total')
#        plt.plot(d[:, 0], d[:, 2], color='b', linestyle='--',
#                 label='Active (last 90 days)')
#        plt.plot(d[:, 0], d[:, 3], color='r', linestyle='--',
#                 label='New (last 90 days)')
#        plt.legend()
#        plt.tight_layout()
#        outpath = os.path.join(self.workingdir, "users-overview.png")
#        plt.savefig(outpath)
#
#        print('done', flush=True)


    def subset_df_by_date(self, df):

        # select dates between start/end range
        mask = (df.date >= self.st) & (df.date <= self.et)
        df = df.loc[mask]

    def subset_series_by_date(self, series):

        # select dates between start/end range
        mask = (series.index >= self.st) & (series.index <= self.et)
        return series.loc[mask]

    def save(self):

        # save raw data
        print('--> saving raw data')

        # save the activity data for the specified date range
        wb = workbook(self.outxls)
        sheetname = wb.add_sheet('users')

        comments = ['# NOTES',
                    '# Created on %s' % (datetime.now()),
                    '\n']

        # write pandas data
        cols = list(self.df.columns)
#        cols = ['@timestamp', 'usr_created_date',
#                'usr_created_dt_str', 'usr_email', 'usr_firstname', 'usr_id',
#                'usr_last_login_date', 'usr_last_login_dt_str', 'usr_lastname',
#                'usr_organization', 'usr_type', 'days-since-login']

        # write comments
        wb.write_column(0, 0, sheetname, comments)

        row_start = len(comments) + 2
        col = 0
        for col_name in cols:
            print('--> writing %s to xlsx' % col_name)
            data = self.df[col_name].tolist()
            data.insert(0, col_name)
            wb.write_column(row_start, col, sheetname, data)
            col += 1
        wb.save()

    def user_stats(self):

        def next_quarter(dt0):
            dt1 = dt0.replace(day=1)
            dt2 = dt1 + timedelta(days=32 * 4)
            dt3 = dt2.replace(day=1)
            dt4 = dt3 - timedelta(days=1)
            return dt4

        df = self.load_data()

        # calculate cumulative users
        df = df.groupby(pandas.TimeGrouper('d')).count().usr_id.cumsum()
        df.index[-1]

        qt = datetime(2016, 1, 31)
        data = []
        while qt < df.index[-1]:
            dtstr = qt.strftime('%Y-%m-%d')
            data.append([dtstr, df[dtstr]])
            qt = next_quarter(qt)
        last = df.index.max().strftime('%Y-%m-%d')
        data.append([last, df[last]])

        for i in range(1, len(data)):
                users0 = data[i-1][1]
                users1 = data[i][1]
                diff = users1 - users0
                pct = round(diff / (users1) * 100, 2)
                data[i].extend([diff, pct])
        headers = ["Date", "Total Users", "New Users", "Percent Change"]
        print(tabulate(data, headers))


#        print(data)


    def all(self):

        self.users_over_time()
        self.users_active()
        self.users_new()

        # determine if a users is new or retained
        self.df['retained'] = np.where((self.df.active90 == 1)
                                       & (self.df.isnew == 0), 1, 0)

        # plot
        print('--> creating figure: users-combined.png')
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.30)
        plt.ylabel('User Count')
        plt.xlabel('Account Creation Date')
        plt.title('HydroShare Users Summary')

        dfm = self.df.groupby(pandas.TimeGrouper('d')).count().usr_id.cumsum()
        dfm = self.subset_series_by_date(dfm)
        dfm = dfm.fillna(method='pad')
        plt.plot(dfm.index, dfm,
                 color='k', linestyle='--', label='All Users')

        dfm = self.df.groupby(pandas.TimeGrouper('d')).sum().active90.cumsum()
        dfm = self.subset_series_by_date(dfm)
        dfm = dfm.fillna(method='pad')
        plt.plot(dfm.index, dfm,
                 color='b', linestyle='-', label='Active Users - 90 days')

#        dfm = self.df.groupby(pandas.TimeGrouper('d')).sum().isnew.cumsum()
#        dfm = dfm.fillna(method='pad')
#        plt.plot(dfm.index, dfm,
#                 color='g', linestyle='-', label='New Users')
#
#        dfm = self.df.groupby(pandas.TimeGrouper('d')).sum().retained.cumsum()
#        dfm = dfm.fillna(method='pad')
#        plt.plot(dfm.index, dfm,
#                 color='r', linestyle='-', label='Retained Users')

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)

        outpath = os.path.join(self.workingdir, "users-combined.png")
        plt.savefig(outpath)

        self.df.to_pickle(os.path.join(self.workingdir, 'df.pkl'))




#    def users_over_time(self):
#        """
#        Calculate total users over time
#        workingdir: directory where the users.pkl file is located
#        start_date: start of date range
#        end_date: end of date range
#        """
#
#        # groupby day, and calculate the cumsum
#        dfm = self.df.groupby(pandas.TimeGrouper('W')).count().usr_id.cumsum()
#        dfm = self.subset_series_by_date(dfm)
#
#        # plot
#        print('--> creating figure: users-overview.png')
#        fig = plt.figure()
#        plt.xticks(rotation=45)
#        plt.subplots_adjust(bottom=0.15)
#        plt.ylabel('Number of Total Users')
#        plt.title('HydroShare Users by Date Created')
#        plt.plot(dfm.index, dfm,
#                 color='b', linestyle='-')
#        outpath = os.path.join(self.workingdir, "users-overview.png")
#        plt.savefig(outpath)

    def users_active(self):

        """
        Calculate total users over time
        workingdir: directory where the users.pkl file is located
        start_date: start of date range
        end_date: end of date range
        """

        # determine active status
        self.df['active90'] = (self.df.usr_last_login_date - self.df.usr_created_date).astype('timedelta64[D]')
        self.df.loc[(self.df.active90 > 0) & (self.df.active90 < 91), 'active90'] = 1
        self.df.loc[self.df.active90 != 1, 'active90'] = 0

        # save changes back to global df
        dfm = self.df.copy()

        # groupby day, and calculate the cumsum
        dfm = dfm.groupby(pandas.TimeGrouper('W')).sum().active90.cumsum()
        dfm = self.subset_series_by_date(dfm)

        # plot
        print('--> creating figure: users-active.png')
        fig = plt.figure()
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.15)
        plt.ylabel('Number of Total Users')
        plt.xlabel('Account Creation Date')
        plt.title('Users Active in last 90 Days')
        plt.plot(dfm.index, dfm,
                 color='b', linestyle='-')
        outpath = os.path.join(self.workingdir, "users-active.png")
        plt.savefig(outpath)

    def users_new(self):

        """
        Calculate total new users
        """

        # determine if they are new
        self.df['isnew'] = (datetime.today() - self.df.usr_created_date).astype('timedelta64[D]')
        self.df.loc[(self.df.isnew >= 0) & (self.df.isnew <= 90), 'isnew'] = 1
        self.df.loc[self.df.isnew != 1, 'isnew'] = 0
        self.df.fillna(0.0)

        # groupby day, and calculate the cumsum
        dfm = self.df.copy()
        dfm = dfm.groupby(pandas.TimeGrouper('W')).sum().isnew.cumsum()
        dfm = self.subset_series_by_date(dfm)

        # plot
        print('--> creating figure: users-new.png')
        fig = plt.figure()
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.15)
        plt.ylabel('Number of Total Users')
        plt.xlabel('Account Creation Date')
        plt.title('Users Active in last 90 Days')
        plt.plot(dfm.index, dfm,
                 color='b', linestyle='-')
        outpath = os.path.join(self.workingdir, "users-new.png")
        plt.savefig(outpath)

