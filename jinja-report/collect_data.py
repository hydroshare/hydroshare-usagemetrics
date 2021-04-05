#!/usr/bin/env python3

import os
import sys
import pandas
import elastic
import argparse
from datetime import datetime


def get_stats_data(users=True, resources=True,
                   activity=True, dirname='.',
                   skip=True, deidentify=False):

    # standard query parameters
    host = 'usagemetrics.hydroshare.org'
    port = '8080'

    ufile = os.path.join(dirname, 'users.pkl')
    ucsv = os.path.join(dirname, 'users.csv')

    rfile = os.path.join(dirname, 'resources.pkl')
    rcsv = os.path.join(dirname, 'resources.csv')

    afile = os.path.join(dirname, 'activity.pkl')
    acsv = os.path.join(dirname, 'activity.csv')

    report_dt_str = datetime.today().strftime('%m/%d/%Y')

    uindex = '*user*latest*'
    uquery = f'rpt_dt_str:"{report_dt_str}"'

    rindex = '*resource*latest*'
    rquery = f'rpt_dt_str:"{report_dt_str}"'

    aindex = '*activity*'
    aquery = '-user_id:None AND -action:visit'

    # get user data
    if users:
        drop = []
        if deidentify:
            drop = ['usr_email', 'usr_firstname', 'usr_lastname']
        if os.path.exists(ufile) and skip:
            print(f'--> file exists: {ufile}...skipping')
        else:
            print('DOWNLOADING USER DATA')
            kwargs = dict(query=uquery,
                          port=port,
                          index=uindex,
                          outpik=ufile,
                          outfile=ucsv,
                          drop=drop)
            for k, v in kwargs.items():
                print(f'--> {k}: {v}')

            elastic.get_es_data(host, **kwargs)
    else:
        ufile = ''

    # get resource data
    if resources:
        if os.path.exists(rfile) and skip:
            print(f'--> file exists: {rfile}...skipping')
        else:
            print('--> DOWNLOADING RESOURCE DATA')
            kwargs = dict(query=rquery,
                          port=port,
                          index=rindex,
                          outpik=rfile,
                          outfile=rcsv,
                          rename_cols={'id': 'resource_id'})
            for k, v in kwargs.items():
                print(f'--> {k}: {v}')

            elastic.get_es_data(host, **kwargs)
    else:
        rfile = ''

    # get activity data
    if activity:
        if deidentify:
            drop = ['usr']
        if os.path.exists(afile) and skip:
            print(f'--> file exists: {afile}...skipping')
        else:
            print('--> downloading activity metrics')
            elastic.get_es_data(host, port, aindex, query=aquery,
                                outpik=afile, outfile=acsv, drop=drop)
    else:
        afile = ''

    print('--> output files produced')
    print(' -> %s' % ufile)
    print(' -> %s' % rfile)
    print(' -> %s' % afile)
    print('\n')

    return dict(users=ufile,
                resources=rfile,
                activity=afile)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        help='skip data collection if it already exists',
                        action='store_true',
                        default=False)
    parser.add_argument('-d',
                        help='directory to save data',
                        default=datetime.now().strftime('%m.%d.%Y'))
    parser.add_argument('--de-identify',
                        help='de-identify the raw data',
                        action='store_true',
                        default=False)

    args = parser.parse_args()

    # create a directory for these data
    datadir = args.d

#    if args.s:
#        if os.path.exists(datadir):
#            print('Directory already exists, skipping')
#            sys.exit(0)

    if not os.path.exists(datadir):
        os.makedirs(datadir)

#    i = 2
#    while os.path.exists(datadir):
#        dirs = datadir.split()
#        dirs[0] = dirs[0][:10] + '_%d' % i
#        i += 1
#        datadir = '/'.join(dirs)
#    os.makedirs(datadir)

    print('Metrics will be saved into: %s' % datadir)

    data = get_stats_data(dirname=datadir,
                          skip=args.s,
                          deidentify=args.de_identify)

