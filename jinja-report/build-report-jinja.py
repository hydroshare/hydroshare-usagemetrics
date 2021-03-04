#!/usr/bin/env python3


import os
import sys
import yaml
import shutil
import jinja2
import argparse
from datetime import datetime
import series_models as models
from subprocess import Popen, PIPE

import plot
import users


class modules():
    module_map = {'user': users}

    def lookup(self, type):
        return self.module_map.get(type, None)


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

    p = argparse.ArgumentParser()
    p.add_argument('yaml_data',
                   help='yaml configuration file')
    args = p.parse_args()

    with open(args.yaml_data, 'r') as f:
        dat = yaml.load(f, Loader=yaml.FullLoader)

    # parse report parameters
    report_params = dat.get('report')

    # check that the input and output directories exist
    indir = os.path.join(report_params.get('input_directory'), 'data')
    if not os.path.exists(indir):
        print('Could not located the input directory, so I will create it '
              f'and collect data.')
        run(['collect_data.py',
             '-s',
             '-d',
             indir,
             '--de-identify'])
    outdir = os.path.abspath(report_params['output_directory'])
    if not os.path.exists(outdir):
        print('Could not find output directory so I\'m making one: '
              f'{outdir}')
        os.makedirs(outdir)

    # loop through metrics args and parse them
    metrics = {}
    for k, v in dat.get('metrics', {}).items():
        mtype = v.pop('metric_type', None)
        if mtype is None:
            # no metric type was given, skip
            continue

        # instantiate figure
        fig_config = v.pop('figure_configuration', None)
        if fig_config is not None:
            figure = getattr(models, 'Figure')(**fig_config)
            v['figure'] = figure

        # instantiate mtype class
        _class = getattr(models, mtype)
        v['input_directory'] = indir

        metrics[k] = _class(**v)

    # loop through parsed metrics and generate figures
    mods = modules()
    data = []
    import pdb; pdb.set_trace()
    for metric_name, metric_data in metrics.items():
        series = metric_data.get_series()
        figure_data = metric_data.figure

        # generate the figure
        module = mods.lookup(metric_data.__class__.__name__)
        plots = []
        for series_type, series_data in series.items():
            method = getattr(module, series_type)
            plots.append(method(**series_data))

        # generate plots for each metric.
        method = getattr(plot, series_data['figure'].type)
        outpath = os.path.join(outdir,
                               series_data['figure_name'] + '.png')
        method(plots, outpath,
               rcParams=series_data['figure'].rcParams,
               axis_dict=series_data['figure'].axis,
               figure_dict=series_data['figure'].figure)
        data.append({'caption': series_data['figure_caption'],
                     'img_path': outpath})

    Loader = jinja2.FileSystemLoader('./templates')
    env = jinja2.Environment(loader=Loader)
    template = env.get_template('template.html')
    with open(os.path.join(outdir, 'report.html'), 'w') as f:
        f.write(template.render(dat=data))


