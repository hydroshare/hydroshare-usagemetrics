#!/usr/bin/env python3



"""
Utility functions
"""

import pandas


def save_data_to_csv(data_dict, index='date'):
    for k, v in data_dict.items():
        dfs = []
        for d in v:
            # convert series to frame if necessary
            if type(d) == pandas.Series:
                d = pandas.DataFrame(d)

#            # set the index
#            d.set_index('date', inplace=True)

            dfs.append(d)

        # combine dataframes
        df_concat = pandas.concat(dfs, axis=1)

        df_concat.to_csv(k)

        print(f'--> data saved to: {k}')
