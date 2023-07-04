#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:22:53 2023

@author: hog
"""



from sentinelsat import SentinelAPI
from datetime import datetime
import pandas as pd
import os


# Information mandatory to automatically acquire data
# from ESA's open data hub 
api_url      = 'https://scihub.copernicus.eu/dhus'
this_user    = 'Zefram'
this_pw      = 'wdlo1645'

footprint = "Intersects(POLYGON((55.104999600088824 -20.753694929672324,\
    55.986652432120074 -20.753694929672324,\
        55.986652432120074 -21.499223270882567,\
            55.104999600088824 -21.499223270882567,\
                55.104999600088824 -20.753694929672324)))"


start_date  = '20230101'
sensor_mode = 'SM'
## end information 


## Check local data repository for newest file
base_dir = os.getcwd()
os.chdir('data')

local_repo = []
for i in os.listdir():
    if os.path.isfile(i):
        local_scene = datetime.strptime(i[17:25],'%Y%m%d')
        local_repo.append(local_scene)
        
os.chdir(base_dir)
## end check local

## Check ESA's open data hub for latest data
api = SentinelAPI(this_user, this_pw, api_url)

query_kwargs = {'footprint': footprint,
        'platformname': 'Sentinel-1',
        'date': (start_date, 'NOW'),
        'producttype':'SLC',
        'sensoroperationalmode':sensor_mode}


info = api.query(**query_kwargs) 
## end check

## Check if ESA's latest scene is in local repo 
## If not: download latest scene from ESA
scenes_df = api.to_dataframe(info)
scenes_df.sort_values(by=['beginposition'])
scenes_df =scenes_df.reset_index(drop=True)
latest = scenes_df.iloc[0]['title'][17:25]
latest_scene = datetime.strptime(latest,'%Y%m%d')

if latest_scene in local_repo:
    print(scenes_df.iloc[0]['title'], ' already in local repository.')
else:
    print('Would like to download ', scenes_df.iloc[0]['title'])
    os.chdir('data')

##

# if to_be_downloaded:
#     api.download(newest['uuid'])
    

