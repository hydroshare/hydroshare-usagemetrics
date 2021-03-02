#!/usr/bin/env python3

from dataclasses import dataclass

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
class user():
    figure_name: str = ''
    figure_title: str = ''
    executable: str = 'users.py'
    active_range: int = 30
    step: str = 1
    all: bool = False
    total: bool = False
    new: bool = False

    def run_cmd(self):
        cmd = [f'{self.executable}',
               f'--active-range={self.active_range}',
               f'--filename={self.figure_name}.png',
               f'--figure-title={self.figure_title}',
               f'--step={self.step}']
        if self.all:
            cmd.append('-a')
        if self.total:
            cmd.append('-t')
        if self.new:
            cmd.append('-n')

        return cmd


@dataclass
class resource():
    pass
