#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:22:53 2023

This module depends on: sentinelsat and snappy

@Version: 1.0
@author: hog
"""


def read_environment():
    
    import os
    base_dir = os.getcwd()
    os.chdir('cohdet_aux')
    cohdet_env = {}
    with open("cohdet_env") as f:
        for line in f:
            (key, val) = line.split('=')
            cohdet_env[key.strip()] = val.strip()
    os.chdir(base_dir)
    return cohdet_env
    
def write_environment(in_envd):
    import os
    base_dir = os.getcwd()
    os.chdir('cohdet_aux')
    with open('cohdet_env','w') as file:
        for k in in_envd.keys():
            file.write("%s=%s\n" % (k, in_envd[k]))
    os.chdir(base_dir)


def preprocess_scene(scene_name, footprint, band_name):
    """
    function aimes to download a precise orbit file from ESA's GNSS-hub
    and apply it a scene before subsetting the scene to the AOI and
    writing it to disk
    
    Parameters
    ----------
    scene_name : string
        name of a zip-file containing Sentinel 1 SLC data
        name must follow the ESA naming convention as
        explained here: https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar/naming-conventions   
    footprint : WKT string
        string describing a polygon around the area of interest in
        wkt (well known text format)
    bandname : string
        the band that will be used, should be the VV one

    Returns
    -------
    0  error code, no errors
    -1 error status unknown 
    x  any other number: error
    
    Output
    ------
    preprocessed SAR scene
        location: data directory
        name: scene_date
        format: beam-dim

    """
    import snappy
    from snappy import ProductIO, GPF, WKTReader
    SAR_image = ProductIO.readProduct(scene_name)
    
    ## Apply orbit file
    print('Apply orbit file')
    orbit_HashMap = snappy.jpy.get_type('java.util.HashMap')
    parameters = orbit_HashMap()
    parameters.put('Apply-Orbit-File', True)
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', '3')
    parameters.put('continueOnFail', 'false')
    SAR_image_orb = GPF.createProduct('Apply-Orbit-File', parameters, SAR_image)
    print('Done orbit file')
    
    print('Subsetting')
    geom = WKTReader().read(footprint)
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    #GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geom)
    #parameters.put('bandNames', band_name)
    SAR_image_subset = GPF.createProduct('Subset', parameters, SAR_image_orb)
    ProductIO.writeProduct(SAR_image_subset, scene_name[17:25]+'_subset', 'BEAM-DIMAP')
    print('Done subsetting')
    return -1



def update_repo():
    """
    function to download new data
    checks against "latest" entry in cohdet_env

    Returns
    -------
    None.
    
    Output
    ------
    Writes new satellite scene to data directory on disk

    """
    from sentinelsat import SentinelAPI
    from datetime import datetime
    import pandas as pd
    import os
    import sys
    
    base_dir = os.getcwd()
     
    envd    = read_environment()
    
    api = SentinelAPI(envd['this_user'],\
                      envd['this_pw'],\
                          envd['api_url'])
    
    footprint = 'Intersects('+envd['footprint']+')'
    
    query_kwargs = {'footprint': footprint,
            'platformname': 'Sentinel-1',
            'date': (envd['start'], 'NOW'),
            'producttype':'SLC',
            'sensoroperationalmode':envd['sensor_mode']}
    
    try:
        info = api.query(**query_kwargs)
    except Exception as e:
        sys.exit(e)
        
        
        
    scenes_df = api.to_dataframe(info)
    scenes_df.sort_values(by=['beginposition'])
    scenes_df =scenes_df.reset_index(drop=True)
   
    
    if read_environment()['latest'] in scenes_df.iloc[0]['title']:
        print('No new data')
    else:
        # for a better error handling see
        # https://stackoverflow.com/questions/44893461/problems-exiting-from-python-using-ipython-spyder
        # and
        # https://sentinelsat.readthedocs.io/en/stable/api_reference.html#module-sentinelsat.exceptions
        print('Would like to download ', scenes_df.iloc[0]['title'])
        os.chdir('data')
        
        try:
            api.download(scenes_df.iloc[0]['uuid'])
        except Exception as e:
            sys.exit(e)
       
        os.chdir(base_dir)
        envd['latest'] = scenes_df.iloc[0]['title'][17:25]
        write_environment(envd)