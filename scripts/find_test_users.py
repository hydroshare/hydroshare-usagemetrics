#!/usr/bin/env python3

import os
import pandas as pd
from tabulate import tabulate
import re

users_pkl = 'users.pkl'
resources_pkl = 'resources.pkl'
activity_pkl = 'activity.pkl'
users_csv = 'userdata.csv'

query_data = False
for f in [users_pkl, resources_pkl, activity_pkl]:
    if not os.path.exists(f):
        query_data = True
        break

if query_data:
    import getdata
    getdata.get_stats_data()

print('--> loading users.pkl')
df = pd.read_pickle(users_pkl)

print('--> loading resources.pkl')
dfr = pd.read_pickle(resources_pkl)

print('--> loading activity.pkl')
dfa = pd.read_pickle(activity_pkl)

print('--> loading usernames')
ud = pd.read_csv(users_csv, dtype={'usr_id': str})
df = pd.merge(df, ud, on='usr_id', how='inner')

test_account_list = []


def get_test_users(patterns):

    test_accounts = pd.DataFrame()
    search_cols = ['username', 'usr_firstname', 'usr_lastname']

    print('Search pattern: %s' % patterns)
    print('Searching columns: %s' % ', '.join(search_cols))

    for col in search_cols:

        # find all matches
        matches = df[df[col].str.contains(patterns,
                                          flags=re.IGNORECASE,
                                          regex=True,
                                          na=False)]

        test_accounts = pd.concat([test_accounts, matches])
        test_accounts = test_accounts.drop_duplicates().reset_index(drop=True)

    # create a new dataframe with only the columns used to match
    results = pd.DataFrame(test_accounts, columns=search_cols).values.tolist()
    table = tabulate(results, headers=search_cols, tablefmt='psql')
    print(table)

    ids = list(test_accounts.usr_id)
    return ids


def calculate_activity_stats(df, ids):

    results = []

    # subset of df from test users
    dft = df[df.user_id.isin(ids)]
    pct = 100 * len(dft)/len(df)
    results.append(['ALL USERS', len(dft), len(df), pct])

    methods = set(df.action)
#    methods = ['visit']
    for m in methods:
        df_test_method = dft[dft.action == m]
        df_method = df[df.action == m]
        pct = 100 * len(df_test_method)/len(df_method)
        results.append([m.upper(), len(df_test_method), len(df_method), pct])

    table = tabulate(results,
                     headers=['Attribute',
                              'Test Users Count',
                              'Total Count',
                              'Percent of Total'],
                     tablefmt='psql')
    print(table)


def calculate_resource_stats(df, ids):

    results = []

    # subset of df for test users
    dft = df[df.usr_id.isin(ids)]
    pct = 100 * len(dft)/len(df)
    results.append(['ALL RESOURCES', len(dft), len(df), pct])

    # count by resource type
    types = set(dft.res_type)
    for t in types:
        df_test_rtype = dft[dft.res_type == t]
        df_rtype = df[df.res_type == t]
        pct = 100 * len(df_test_rtype)/len(df_rtype)
        results.append([t.upper(), len(df_test_rtype), len(df_rtype),
                        pct])

    table = tabulate(results,
                     headers=['Attribute',
                              'Test Users Count',
                              'Total Count',
                              'Percent of Total'],
                     tablefmt='psql')
    print(table)


def calculate_app_activity(df, ids):

    results = []

    # subset of df from test users
    dft = df[df.user_id.isin(ids)]
    dft = dft[dft.action == 'app_launch']
    dfapp = df[df.action == 'app_launch']
    pct = 100 * len(dft)/len(dfapp)
    results.append(['ALL APP LAUNCHES', len(dft), len(dfapp), pct])

    apps = set(dft.name)
    for app in apps:
        df_test_app = dft[dft.name == app]
        df_app = dfapp[dfapp.name == app]
        pct = 100 * len(df_test_app)/len(df_app)
        results.append([app.upper(), len(df_test_app), len(df_app), pct])

    table = tabulate(results,
                     headers=['App Name',
                              'Test Users Count',
                              'Total Count',
                              'Percent of Total'],
                     tablefmt='psql')
    print(table)



# determine test users
patterns = '^demo.*$|^.*test.*$'
print('\nTest User Accounts')
ids = get_test_users(patterns)

# determine activity from test accounts
print('\nActivity from Test Users')
calculate_activity_stats(dfa, ids)

# determine resources from test accounts
print('\nResources from Test Users')
calculate_resource_stats(dfr, ids)

# determine app activity by test users
print('\nApp activity from Test Users')
calculate_app_activity(dfa, ids)

# isolate resources from test accounts users
#test_resources = dfr[dfr.usr_id.isin(ids)]
#print('%d of %d resources are from test accounts ==> %3.5f %%' %
#      (len(test_resources),
#       len(dfr),
#       100 * (len(test_resources)/len(dfr))))

# isolate resources that contain 'test' in the title


# isolate resources that contain 'test' in the abstract


# isolate activity from test accounts










