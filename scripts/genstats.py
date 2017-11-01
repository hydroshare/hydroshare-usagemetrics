#!/usr/bin/env python3

import os
import sys
import pandas
import getdata
from tabulate import tabulate
import argparse


def pretty_print_df(df):
    print(tabulate(df, headers='keys', tablefmt='psql'))


def genstats(nrows, display=1, csvout=1):
    u = pandas.read_pickle(stats['users'])
    r = pandas.read_pickle(stats['resources'])
    a = pandas.read_pickle(stats['activity'])

    # convert user date strings to dates
    u['usr_created_dt'] = u['usr_created_date'].astype('datetime64[ns]')
    u['usr_last_login_dt'] = u['usr_last_login_date'].astype('datetime64[ns]')
    u['report_dt'] = u['report_date'].astype('datetime64[ns]')

    # calculate date metrics
    u['days_since_login'] = (u['report_dt'] - u['usr_last_login_dt']).dt.days
#    u['days_logged_since_account_creation'] = (u['usr_created_dt'] - u['usr_last_login_dt']).dt.days
    u['days_since_account_creation'] = (u['report_dt'] - u['usr_created_dt']).dt.days

    preview_cols = ['usr_id', 'usr_firstname', 'usr_lastname']
    output_cols = ['usr_id', 'usr_firstname', 'usr_lastname', 'usr_type',
                   'usr_organization', 'usr_created_date',
                   'usr_last_login_date', 'days_since_login',
                   'days_since_account_creation']

    # get top users by number of resources
    print('--> calculating top users by resource count')
    counts = r.groupby(['usr_id'], as_index=False).count()
    scounts = counts.sort_values(['res_date_created'], ascending=[0])
    scounts = scounts[['usr_id', 'res_date_created']]
    scounts = scounts.rename(columns={'res_date_created': 'resource_count'})
    top = scounts.head(nrows)
#    top = pandas.merge(top, u, on='usr_id', how='left')
    top = pandas.merge(top, u, on='usr_id', how='outer')
    top.resource_count.fillna(value=0, inplace=1)
    if display:
        print('\nTop %d Users by Resource Count' % nrows)
        pretty_print_df(top[preview_cols + ['resource_count']])
    if csvout:
        print('--> saving to resource-count.csv')
        top[output_cols + ['resource_count']].to_csv('resource-count.csv')

    # get top users by resource size
    print('--> calculating top users by resource size')
    sizes = r.groupby(['usr_id'], as_index=False).sum()
    ssizes = sizes.sort_values(['res_size'], ascending=[0])
    ssizes = ssizes[['usr_id', 'res_size']]
    ssizes.loc[:, 'res_size'] /= 1000000000
    ssizes = ssizes.rename(columns={'res_size': 'resource size GB'})
    top = ssizes.head(nrows)
#    top = pandas.merge(top, u, on='usr_id', how='left')
    top = pandas.merge(top, u, on='usr_id', how='outer')
    top['resource size GB'].fillna(value=0, inplace=1)
    if display:
        print('\nTop %d Users by Resource Size' % nrows)
        pretty_print_df(top[preview_cols + ['resource size GB']])
    if csvout:
        print('--> saving to resource-size.csv')
        top[output_cols + ['resource size GB']].to_csv('resource-size.csv')

    # get the top users by number of sessions
    print('--> calculating top users by sessions')
    sessions = a[a.action == 'begin_session'].groupby('user_id', as_index=False).agg({'action': 'count'})
    ssessions = sessions.sort_values('action', ascending=0)
    top = ssessions.head(nrows)
    top = top.rename(columns={'user_id': 'usr_id', 'action': 'session count'})
#    top = pandas.merge(top, u, on='usr_id', how='left')
    top = pandas.merge(top, u, on='usr_id', how='outer')
    top['session count'].fillna(value=0, inplace=1)
    if display:
        print('\nTop %d Users by Number of Sessions' % nrows)
        pretty_print_df(top[preview_cols + ['session count']])
    if csvout:
        print('--> saving to session-count.csv')
        top[output_cols + ['session count']].to_csv('session-count.csv')

    # get the top users by number of published resources
    print('--> calculating top users by resources published')
    pub = r[r.res_pub_status == 'published']
    pub_grp = pub.groupby(['usr_id'], as_index=0).count()
    pub_srt = pub_grp.sort_values(['res_pub_status'], ascending=[0])
    top = pub_srt.head(nrows)
    top = top[['usr_id', 'res_pub_status']]
    top = top.rename(columns={'res_pub_status': 'total published'})
#    top = pandas.merge(top, u, on='usr_id', how='left')
    top = pandas.merge(top, u, on='usr_id', how='outer')
    top['total published'].fillna(value=0, inplace=1)
    if display:
        print('\nTop %d Users by Resources Published' % nrows)
        pretty_print_df(top[preview_cols + ['total published']])
    if csvout:
        print('--> saving to published-count.csv')
        top[output_cols + ['total published']].to_csv('published-count.csv')

    print('\n')


req_files = ['users.pkl',
             'resources.pkl',
             'activity.pkl',
             'combined-stats.pkl']

missing_count = 0
print('checking for required files...')
for f in req_files:
    if os.path.exists(f):
        print('--> %s... found' % f)
    else:
        print('--> %s... missing' % f)
        missing_count += 1

if missing_count > 0:
    print(60*'-')
    res = input('Missing one or more files (see above).  These data must be\n'
                're-download before continuing. Do you want to proceed [Y/n]? '
                )
    print(60*'-')
    if res == 'n':
        sys.exit(1)

    # remove files
    for f in req_files:
        if os.path.exists(f):
            os.remove(f)

    # re-download the required files
    stats = getdata.get_stats_data()

else:
    stats = dict(zip(['users',
                      'resources',
                      'activity',
                      'combined'], req_files))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate usage summary tables")
    parser.add_argument('-r', '--nrows', required=0, default=30, type=int,
                        help='number of rows to print')
    parser.add_argument('-d', '--display', required=0, default=1, type=int,
                        help='display statistic preview')
    parser.add_argument('-o', '--output', required=0, default=1, type=int,
                        help='output statistics to file')
    args = parser.parse_args()
    genstats(args.nrows, args.display, args.output)

