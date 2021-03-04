#!/usr/bin/env python3

import pytz
from typing import List
from datetime import datetime
from dataclasses import dataclass, field


"""
This file contains the class models for each series type
"""


@dataclass
class report():
    output_dir: str = None
    input_dir: str = None

    def __post_init__(self):
        if self.output_dir is None:
            raise ValueError('Missing required field: "output_dir"')
        if self.input_dir is None:
            raise ValueError('Missing required field: "input_dir"')


@dataclass
class Series():
    type: str
    color: str = 'b'
    linestyle: str = '-'


@dataclass
class Figure():
    axis: dict = field(default_factory=dict)
    figure: dict = field(default_factory=dict)
    rcParams: dict = field(default_factory=dict)
    type: str = 'line'


@dataclass
class user():
    series: List[Series]
    figure: Figure = field(default_factory=Figure)
    figure_name: str = ''
    figure_caption: str = ''
    input_directory: str = '.'
    start_time: str = '01-01-2000'
    end_time: str = '01-01-2025'
    executable: str = 'users.py'
    active_range: int = 30
    step: str = 1

    def get_series(self):

        s = {}

        # set timezone to UTC
        self.start_time = pytz.utc.localize(datetime.strptime(self.start_time, '%m-%d-%Y'))
        self.end_time = pytz.utc.localize(datetime.strptime(self.end_time, '%m-%d-%Y'))

#        args = [self.input_directory,
#                st, et,
#                self.active_range,
#                self.step]
        
        # get the class attributes that will be returned
        kwargs = self.__dict__
        
#        fig_config = kwargs.pop('figure')
#        fig_config = fig_config.get_config()
#        kwargs['figure_configuration'] = fig_config

        # add each series individually
        series = kwargs.pop('series')
        for seri in series:
            series_kwargs = kwargs.copy()
            series_kwargs.update(seri)
            s[seri.pop('type')] = series_kwargs

        return s

        
#    def __post_init__(self):
#                s[k]['st'] = datetime.strptime(self.start_time, '%m-%d-%Y')
#                s[k]['et'] = datetime.strptime(self.end_time, '%m-%d-%Y')
#                s[k]['active
#            
#    def run_cmd(self):
#        cmd = [f'{self.executable}',
#               f'--active-range={self.active_range}',
#               f'--filename={self.figure_name}.png',
#               f'--figure-title={self.figure_title}',
#               f'--step={self.step}']
#        if self.all:
#            cmd.append('-a')
#        if self.total:
#            cmd.append('-t')
#        if self.new:
#            cmd.append('-n')
#
#        return cmd
#

@dataclass
class resource():
    pass
