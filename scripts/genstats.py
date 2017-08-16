#!/usr/bin/env python3

import os
import sys
import pandas
import getdata
from tabulate import tabulate

def pretty_print_df(df):
  print(tabulate(df, headers='keys', tablefmt='psql'))

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

u = pandas.read_pickle(stats['users'])
r = pandas.read_pickle(stats['resources'])
a = pandas.read_pickle(stats['activity'])
j = r.join(u, on='usr_id', how='left', lsuffix='_[r]', rsuffix='_[u]')

# get top users by number of resources
print('\n'+30*'-'+'\nTop 10 Users by Resource Count')
counts = r.groupby(['usr_id'], as_index=False).count()
scounts = counts.sort_values(['res_date_created'], ascending=[0])
scounts = scounts[['usr_id', 'res_date_created']]
scounts = scounts.rename(columns={'res_date_created': 'resource_count'})
top = scounts.head(10)
top = pandas.merge(top, u, on='usr_id', how='left')
pretty_print_df(top[['usr_id', 'usr_firstname', 'usr_lastname', 'resource_count']])

# get top users by resource size
print('\n'+30*'-'+'\nTop 10 Users by Resource Size')
sizes = r.groupby(['usr_id'], as_index=False).sum()
ssizes = sizes.sort_values(['res_size'], ascending=[0])
ssizes = ssizes[['usr_id', 'res_size']]
ssizes.loc[:, 'res_size'] /= 1000000000
ssizes = ssizes.rename(columns={'res_size': 'resource size GB'})
top = ssizes.head(10)
top = pandas.merge(top, u, on='usr_id', how='left')
pretty_print_df(top[['usr_id', 'usr_firstname', 'usr_lastname', 'resource size GB']])

# get the top users by number of sessions
print('\n'+34*'-'+'\nTop 10 Users by Number of Sessions')
sessions = a[a.action == 'begin_session'].groupby('user_id', as_index=False).agg({'action': 'count'})

ssessions = sessions.sort_values('action', ascending=0)
top = ssessions.head(10)
top = top.rename(columns={'user_id': 'usr_id', 'action':'session count'})
top = pandas.merge(top, u, on='usr_id', how='left')

# display the results
pretty_print_df(top[['usr_id', 'usr_firstname', 'usr_lastname', 'session count']])

# get the top users by number of published resources
print('\n'+36*'-'+'\nTop 10 Users by Resources Published')
pub = r[r.res_pub_status == 'published']
pub_grp = pub.groupby(['usr_id'], as_index=0).count()
pub_srt = pub_grp.sort_values(['res_pub_status'], ascending=[0])
top = pub_srt.head(10)
top = top[['usr_id', 'res_pub_status']]
top = top.rename(columns={'res_pub_status': 'total published'})
top = pandas.merge(top, u, on='usr_id', how='left')
pretty_print_df(top[['usr_id', 'usr_firstname', 'usr_lastname', 'total published']])

print('\n')
