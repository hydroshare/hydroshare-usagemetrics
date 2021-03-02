#!/usr/bin/env python3


import os
import sys
import yaml
import shutil
import argparse
from datetime import datetime
import series_models as models
from subprocess import Popen, PIPE


def read_config(yaml_path):
    """
    reads yaml configuration file and returns build arguments
    """
    with open(yaml_path, "r") as f:
        yaml_data = yaml.load(f, Loader=yaml.FullLoader)

    # todo: insert error checking
    return yaml_data


def output_exists(cmd):
    fname = None
    wrk = ''
    for c in cmd:
        if '--filename' in c:
            fname = c.split('=')[-1]
        if '--working-dir' in c:
            wrk = c.split('=')[-1]

    if fname is not None:
        if os.path.exists(os.path.join(wrk, fname)):
            return True
    return False


def run(command):
    if output_exists(command):
        print('.. skipping bc output already exists')
        return

    cmd = [sys.executable] + command

    p = Popen(cmd, stderr=PIPE)
    while True:
        out = p.stderr.read(1).decode('utf-8')
        if out == '' and p.poll() is not None:
            break
        if out != '':
            sys.stdout.write(out)
            sys.stdout.flush()


if __name__ == '__main__':

    default_data_dir = datetime.strftime(datetime.today(), '%m.%d.%Y')
    default_out_dir = os.getcwd()

    p = argparse.ArgumentParser()
    p.add_argument('yaml_data',
                   help='yaml configuration file')
    args = p.parse_args()

    with open(args.yaml_data, 'r') as f:
        dat = yaml.load(f, Loader=yaml.FullLoader)

    # parse report parameters
    report_params = dat.get('report')

    # check that the input and output directories exist
    if not os.path.exists(report_params['input_dir']):
        print('ERROR: Could not located the input directory: '
              f'{report_params["input_dir"]}')
        sys.exit(1)
    outdir = os.path.abspath(report_params['output_dir'])
    if not os.path.exists(outdir):
        print('Could not find output directory so I\'m making one: '
              f'{outdir}')
        os.makedirs(outdir)

    # loop through metrics args and parse them
    metrics = {}
    for k, v in dat.get('metrics', {}).items():
        _class = getattr(models, k)
        metrics[k] = _class(**v)

    # loop through parsed metrics and generate figures
#    import pdb; pdb.set_trace()
    for k, v in metrics.items():
        # set the output figure to save in the output_directory
        v.figure_name = os.path.join(report_params['output_dir'],
                                     v.figure_name)
        cmd = v.run_cmd()
        cmd.append(f'--working-dir={report_params["input_dir"]}')
        print(cmd)
        run(cmd)

    # generate report document


#    # build the output directory
#    wrkdir = datetime.strftime(datetime.today(), '%m.%d.%Y')
#    report_dir = os.path.join(wrkdir, 'tex')
#    data_dir = os.path.join(wrkdir, 'data')
#    report_fn = f'%s-hydroshare-metrics' % \
#                datetime.strftime(datetime.today(), '%Y.%m.%d')
#
#    fig_dir = os.path.join(wrkdir, 'fig')
#    if not os.path.exists(fig_dir):
#        os.makedirs(fig_dir)
#
#    if not os.path.exists(report_dir):
#        os.makedirs(report_dir)
#
##    generate_figures(data_dir, '../fig')
##    create_report(report_dir, fig_dir, report_fn=report_fn)
##    pdf = f'%s.pdf' % report_fn
##    shutil.move(join(report_dir, pdf),
##                join(wrkdir, pdf))
