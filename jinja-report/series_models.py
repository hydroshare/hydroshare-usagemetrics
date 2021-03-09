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
    creator: str = ''
    date_created: datetime = datetime.today()
    description: str = ''
    title: str = ''

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
    caption: str = ''
    title: str = ''
    annotate: bool = False
    grid: bool = False
    legend: bool = False


class Base():
    def get_series(self):
        s = {}

        # set timezone to UTC
        self.start_time = pytz.utc.localize(datetime.strptime(self.start_time, '%m-%d-%Y'))
        self.end_time = pytz.utc.localize(datetime.strptime(self.end_time, '%m-%d-%Y'))

        # get the class attributes that will be returned
        kwargs = self.__dict__

        # add each series individually
        series = kwargs.pop('series')
        for seri in series:
            series_kwargs = kwargs.copy()
            series_kwargs.update(seri)
            s[seri.pop('type')] = series_kwargs

        return s

@dataclass
class user(Base):
    series: List[Series]
    figure: Figure = field(default_factory=Figure)
    input_directory: str = '.'
    start_time: str = '01-01-2000'
    end_time: str = '01-01-2025'
    active_range: int = 30
    step: str = 1
    save_data: bool = False


@dataclass
class resource(Base):
    series: List[Series]
    figure: Figure = field(default_factory=Figure)
    input_directory: str = '.'
    start_time: str = '01-01-2000'
    end_time: str = '01-01-2025'
    save_data: bool = False
    aggregation: str = '1W'


@dataclass
class organization(Base):
    series: List[Series]
    figure: Figure = field(default_factory=Figure)
    input_directory: str = '.'
    start_time: str = '01-01-2000'
    end_time: str = '01-01-2025'
    save_data: bool = False
    aggregation: str = '1W'
