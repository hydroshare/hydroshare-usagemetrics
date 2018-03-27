#!/usr/bin/env python3

import os
import pandas
import elastic
from datetime import datetime



def get_stats_data(users=True, resources=True, activity=True, dirname='.'):

    # standard query parameters
    host = 'usagemetrics.hydroshare.org'
    port = '8080'
    ufile = os.path.join(dirname, 'users.pkl')
    rfile = os.path.join(dirname, 'resources.pkl')
    afile = os.path.join(dirname, 'activity.pkl')
    cfile = os.path.join(dirname, 'combined-stats.pkl')
    uindex = '*user*latest*'
    rindex = '*resource*latest*'
    aindex = '*activity*'
    aquery = '-user_id:None AND -action:visit'
#    aquery = '-user_id:None'

#    # clean old files
#    for p in [ufile, rfile, cfile]:
#        if os.path.exists(p):
#            print('--> removing %s' % p)
#            os.remove(p)

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
    u = pandas.read_pickle(ufile)
    r = pandas.read_pickle(rfile)
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
    # create a directory for these data
    dirname = datetime.now().strftime('%m.%d.%Y')

    i = 2
    while os.path.exists(dirname):
        dirname = dirname[:10] + '_%d' % i
        i += 1
    os.makedirs(dirname)

    print('Metrics will be saved into: %s' % dirname)

    get_stats_data(dirname=dirname)
