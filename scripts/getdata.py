#!/usr/bin/env python3

import os
import pandas
import elastic



def get_stats_data(users=True, resources=True, activity=True):

    # standard query parameters
    host = 'usagemetrics.hydroshare.org'
    port = '8080'
    uindex = '*user*latest*'
    ufile = 'users.pkl'
    rindex = '*resource*latest*'
    rfile = 'resources.pkl'
    aindex = '*activity*'
    afile = 'activity.pkl'
    aquery = '-user_id:None AND -action:visit'
#    aquery = '-user_id:None'
    cfile = 'combined-stats.pkl'

    # clean old files
    for p in [ufile, rfile, cfile]:
        if os.path.exists(p):
            print('--> removing %s' % p)
            os.remove(p)

    # get user data
    if users:
        print('--> downloading user metrics')
        elastic.get_es_data(host, port, uindex, outpik=ufile)
    else: 
        ufile = ''

    # get resource data
    if resources:
        print('--> downloading resource metrics')
        elastic.get_es_data(host, port, rindex, outpik=rfile)
    else:
        rfile = ''

    # get activity data
    if activity:
        print('--> downloading activity metrics')
        elastic.get_es_data(host, port, aindex, query=aquery, outpik=afile)
    else:
        afile = ''

    # build and export a combined file
    print('--> combining data')
    u = pandas.read_pickle('users.pkl')
    r = pandas.read_pickle('resources.pkl')
    j = None
    if users and resources:
        j = r.join(u, on='usr_id', how='left', lsuffix='_[r]', rsuffix='_[u]')

        print('--> saving binary file to: %s' % cfile)
        j.to_pickle(cfile)
    else:
        cfile = ''

    print('--> output files produced')
    print(' -> %s' % ufile)
    print(' -> %s' % rfile)
    print(' -> %s' % afile)
    print(' -> %s' % cfile)
    print('\n')

    return dict(users=ufile,
                resources=rfile,
                activity=afile,
                combined=cfile)


if __name__ == '__main__':
    get_stats_data()
