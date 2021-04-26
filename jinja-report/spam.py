#!/usr/bin/env python3


"""
The purpose of these functions are to clean users, resources, and activities
related to known spam users from the historical data
"""

import os
import json
import requests
import pandas as pd


def gather_spam_user_ids(
    working_dir: str, cache: bool = True, use_cache: bool = True
) -> dict:
    """
    Collects spam user ids from a web service that Neal DeBuhr created.
    args:
        working_dir (str): working directory, this is used to look for and
                           save cache files.
        cache (bool):      indicates whether or not to save data for future use
        use_cache (bool):  indicates whether or not to use an existing cache
                           if one exists.
    returns:  resource ids and user ids associated with spam
              accounts, dict{'resources':list[str],
                             'users':list[int]}.
    """

    print('.. collecting spam data')

    # load cache if indicated
    if use_cache:
        spam_res = os.path.join(working_dir, "spam-resources.csv")
        spam_usr = os.path.join(working_dir, "spam-users.csv")
        if os.path.exists(spam_res) and os.path.exists(spam_usr):
            print('.... loading cache')
            spam_data = {}

            spam_data['resources'] = list(pd.read_csv(spam_res, dtype={'resource_id': str}).resource_id.values)
            spam_data['users'] = list(pd.read_csv(spam_usr, dtype={'user_id': str}).user_id.values)

            print('.... completed successfully')
            return spam_data

    # collect spam user ids
    print('.... gathering data from spam.cuahsi.io')
#    url = "https://spam.cuahsi.io/api/v1/summary"
    url = "https://obdv25s585.execute-api.us-east-2.amazonaws.com/users"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(
            (f"Error collecting data from {url}.\n", "Reason: {res.reason}")
        )
    dat = json.loads(res.text)

    # convert values to strings to avoid type errors during filtering later
#    spam_data['resources'] = list(map(str, spam_data['resources']))
    spam_data = {}
    spam_data['users'] = list(map(str, dat))
    spam_data['resources'] = []

    if cache:
        print('.... saving cache')
#        # save spam resources
#        df = pd.DataFrame(spam_data["resources"], columns=["resource_id"])
#        df.to_csv(os.path.join(working_dir, "spam-resources.csv"))

        # save spam users
        #df = pd.DataFrame(spam_data["users"], columns=["user_id"])
        df = pd.DataFrame(spam_data, columns=["user_id"])
        df.to_csv(os.path.join(working_dir, "spam-users.csv"))

    print('.... completed successfully')
    return spam_data


def filter_dataframe(df: pd.DataFrame,
                     working_dir: str,
                     input_col: str = 'usr_id',
                     spam_col: str = 'usr_id') -> list:
    """
    filters users, resources, and activities from the input dataframe based
    on spam user ids collected by `gather_spam_user_ids`.

    args:
        df (dataframe): HydroShare user, resource, or activity data
        working_dir (str): working directory, this is used to look for and
                           save cache files.
        input_col (str): name of the column to filter in the input dataframe.
        spam_col (str): name of the spam column to filter with.
    returns: DataFrame without records related to spam users
    """

    # check that input_col exists in the dataframe
    if input_col not in df.columns:
        msg = (f'Column ({input_col}) does not exist in the input dataframe\n',
               f'Available columns: {",".join(df.columns)}')
        raise Exception(msg)

    # load spam data
    spam_data = gather_spam_user_ids(working_dir)

    # check that spam_col exists in the spam data
    if spam_col not in spam_data.keys():
        msg = (f'Column ({spam_col}) does not exist in spam dataset.\n',
               f'Available spam columns: {",".join(spam_data.keys())}')
        raise Exception(msg)

    # filter data based on the input and spam columns.
    dat = df[~df[input_col].isin(spam_data[spam_col])]

    return dat


if __name__ == '__main__':
    working_dir = '03.26.2021'
#    df = pd.read_pickle(os.path.join(working_dir, 'users.pkl'))
#    df_filtered = filter_dataframe(df,
#                                   working_dir,
#                                   'usr_id',
#                                   'users')
#    df = pd.read_pickle(os.path.join(working_dir, 'activity.pkl'))
#    df_filtered = filter_dataframe(df,
#                                   working_dir,
#                                   'user_id',
#                                   'users')
    df = pd.read_pickle(os.path.join(working_dir, 'resources.pkl'))
    df_filtered = filter_dataframe(df,
                                   working_dir,
                                   'usr_id',
                                   'users')

    print(f'input df: {len(df)} records')
    print(f'output df: {len(df_filtered)} records')
