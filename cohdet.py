#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 11:22:53 2023

This module depends on: sentinelsat and snappy

@Version: 1.0
@author: hog
"""


def read_environment():
    """
    Reads a textfile "cohdet_env" expected to be in the directory
    "cohdet_aux"

    Returns
    -------
    cohdet_env: dictionary containing key-value-pairs discribing 
    the cohdet environment:
        
        base_dir: main working directory containing cohdet.py
        data: data directory
        preprocessed: directory for preprocessed data
        coregistered: directory for coregistered data
        interferograms: directory for interferograms
        collocated: directory for collocated interferograms
        results: directory for final results 
        start: start of observation period (first SLC)
        latest: currently latest SCL (cohdet_aux NEED to be WRITABLE)
        this_user: user's name at ESA's science hub
        this_pw: user's password at ESA's science hub
        footprint: footprint polygon of area of interest as wkt
        sensor_mode: sensor mode 
        api_url: Url of ESA's science hub
    """
    
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

def get_unpreprocessed_scenes():
    """
    function that checks local repos content for being preprocessed, i.e.
    it checks weather there exists a preprocessed file in the directory
    given in cohdet_env under "preprocessed" for every file in 
    cohdet_env directory "data"
    
    
    Returns  
    -------
    unpreprocessed_scenes : list of strings

    """
    
    import os
    
    unpreprocessed_scenes = []
    
    base_dir = os.getcwd()
    
    os.chdir('data')
    local_repo = []
    for i in os.listdir():
        if os.path.isfile(i):
            if i[-3:]=="zip":
                local_repo.append(i)
    
    os.chdir(base_dir)
    os.chdir('preprocessed')
    
    prepro_repo = []
    for i in os.listdir():
        if os.path.isfile(i):
            if i[-3:]=='dim':
                prepro_scene = i[0:8]
                prepro_repo.append(prepro_scene)
    
    os.chdir(base_dir)
    
    for i in local_repo:
        if not i[17:25] in prepro_repo:
            unpreprocessed_scenes.append(i)
    
    return unpreprocessed_scenes
 

    
def do_interferogram(prime_scene, secon_scene):
    """
    do_intergerogram calculates a full interferogram between the 
    two files prime_scene and secon_scene. The parameters used are
    hard coded as can be seen below. It may be a good idea to change
    to a sofcoded version with parametersettings read from cohdet_aux.
    
    do_interferogram calculates the interferogram in a four step procedure:
        1. stack scenes
        2. do cross correlation
        3. warp it!
        4. calculate interferogram

    Parameters
    ----------
    prime_scene : TYPE
        scene used as primary scene
    secon_scene : TYPE
        scene used as scondary scene

    Returns
    -------
    None. (but saves an interferogram to cohdet_env: interferograms)

    """
    import os
    import sys
    import snappy
    from snappy import ProductIO, GPF
    
    base_dir = read_environment()['base_dir']
    prepro_dir = read_environment()['preprocessed']
    suffix = '.dim'
    prime_scene_file = (os.path.join(base_dir, prepro_dir, prime_scene+suffix)).strip()
    secon_scene_file = (os.path.join(base_dir, prepro_dir, secon_scene+suffix)).strip()
    
    print(prime_scene_file)
    print(secon_scene_file)
    
    SAR_image_prime = ProductIO.readProduct(prime_scene_file)
    SAR_image_secon = ProductIO.readProduct(secon_scene_file)
    
    # Stack creation
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('extent','Master')
   
    scenes_to_stack = [SAR_image_prime, SAR_image_secon]
    print('Creating stack ')
    stack = GPF.createProduct("CreateStack",parameters,scenes_to_stack)
    out_scene_file_name = prime_scene[0:8]+'_'+secon_scene[0:8]+'_stack'
    coreg_dir = read_environment()['coregistered']
    out_scene_file = os.path.join(base_dir,coreg_dir, out_scene_file_name)
    print(out_scene_file)
    ProductIO.writeProduct(stack, out_scene_file, 'BEAM-DIMAP')
    
    parameters = HashMap()
    parameters.put('numGCPtoGenerate','5000')
    parameters.put('coarseRegistrationWindowWidth','128')
    parameters.put('coarseRegistrationWindowHeight','128')
    parameters.put('rowInterpFactor','4')
    parameters.put('columnInterpFactor','4')
    parameters.put('maxIteration','10')
    parameters.put('gcpTolerance','0.25')
    parameters.put('applyFineRegistration',True)
    SAR_image_corr = GPF.createProduct("Cross-Correlation",parameters, stack)
    
    Float = snappy.jpy.get_type('java.lang.Float')
    parameters = HashMap()
    parameters.put('rmsThreshold',Float(0.05))
    parameters.put('warpPolynomialOrder',1)
    parameters.put('interpolationMethod','Cubic convolution (6 points)')
    SAR_image_coreg = GPF.createProduct("Warp",parameters,SAR_image_corr)
   
       
    out_scene_file_name = prime_scene[0:8]+'_'+secon_scene[0:8]+'_coreg'
    coreg_dir = read_environment()['coregistered']
    out_scene_file = os.path.join(base_dir,coreg_dir, out_scene_file_name)
    print(out_scene_file)
    ProductIO.writeProduct(SAR_image_coreg, out_scene_file, 'BEAM-DIMAP')
    
    
    parameters = HashMap()
    parameters.put("Subtract flat-earth phase", True)
    parameters.put("Degree of \"Flat Earth\" polynomial", 5)
    parameters.put("Number of \"Flat Earth\" estimation points", 501)
    parameters.put("Orbit interpolation degree", 3)
    parameters.put("Include coherence estimation", True)
    parameters.put("Square Pixel", True)
    parameters.put("Independent Window Sizes", False)
    parameters.put("Coherence Azimuth Window Size", 10)
    parameters.put("Coherence Range Window Size", 11)
    SAR_interferogram = GPF.createProduct("Interferogram", parameters, SAR_image_coreg)
    
    out_scene_file_name = prime_scene[0:8]+'_'+secon_scene[0:8]+'_interferogram'
    coreg_dir = read_environment()['interferograms']
    out_scene_file = os.path.join(base_dir,coreg_dir, out_scene_file_name)
    print(out_scene_file)
    ProductIO.writeProduct(SAR_interferogram, out_scene_file, 'BEAM-DIMAP')
    print('Interferogram: done!')
           
def do_collocation(prime_scene, secon_scene):
    """
    Interferograms have to be collocated ("coregistered") to be used
    as terms in bandmath. This is, what do_collocation does for a named
    pair of interferograms

    Parameters
    ----------
    prime_scene : TYPE
        The interferogram used as primary scene
    secon_scene : TYPE
        The interferogram used as scondary scene

    Returns
    -------
    None. (but saves the collocated interferogramm under cohdet_env: collocated)

    """
    import os
    import sys
    import snappy
    from snappy import ProductIO, GPF
    
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    
    base_dir = read_environment()['base_dir']
    ifg_dir = read_environment()['interferograms']
    suffix = '.dim'
    prime_scene_file = (os.path.join(base_dir, ifg_dir, prime_scene+suffix)).strip()
    secon_scene_file = (os.path.join(base_dir, ifg_dir, secon_scene+suffix)).strip()
    
    
    SAR_image_prime = ProductIO.readProduct(prime_scene_file)
    SAR_image_secon = ProductIO.readProduct(secon_scene_file)
    
    
    sources = HashMap()
    sources.put("master", SAR_image_prime)
    sources.put("slave", SAR_image_secon)
    
    parameters = HashMap()
    parameters.put("targetProductName", 'collocated')
    parameters.put("targetProductType", 'COLLOCATED')
    parameters.put('renameMasterComponents', True)
    parameters.put('renameSlaveComponents', True)
    parameters.put('masterComponentPattern', '${ORIGINAL_NAME}_M')
    parameters.put('slaveComponentPattern', '${ORIGINAL_NAME}_S')
    parameters.put('resamplingType', 'NEAREST_NEIGHBOUR')
    cohdet_collocation = GPF.createProduct("Collocate", parameters, sources)
    out_scene_file_name = prime_scene[0:8]+'_'+secon_scene[0:8]+'_collocate'
    coreg_dir = read_environment()['collocated']
    out_scene_file = os.path.join(base_dir,coreg_dir, out_scene_file_name)
    print(out_scene_file)
    ProductIO.writeProduct(cohdet_collocation, out_scene_file, 'BEAM-DIMAP')
    print('Collocation: done!')
    
    
def mask_coh_diff(collocated_scene):
    import os
    import sys
    import snappy
    from snappy import ProductIO, GPF
    
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    
    base_dir = read_environment()['base_dir']
    col_dir = read_environment()['collocated']
    results_dir = read_environment()['results']
    suffix = '.dim'
    col_scene_file = (os.path.join(base_dir, col_dir, collocated_scene+suffix)).strip()
    
    col_scene = ProductIO.readProduct(col_scene_file)
    col_bands = col_scene.getBandNames()
    
    coh_bands = []
    for i in col_bands:
        if 'coh_' in i:
            coh_bands.append(i)
            
            
    
    parameters = HashMap()
    BandDescriptor = snappy.jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'coh_diff_mask'
    targetBand.type = 'float32'
    targetBand.expression = ('if (('+coh_bands[0]+'> 0.6) and ('+coh_bands[1]+'<='+coh_bands[0]+'*0.4)) then 1 else 0')
    targetBands = snappy.jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
    product = GPF.createProduct('BandMaths',parameters,col_scene)
    
    out_scene_file_name = col_bands[1]+'_'+col_bands[0]
    out_scene_file = os.path.join(base_dir,results_dir, out_scene_file_name)
    print(out_scene_file)
    ProductIO.writeProduct(product, out_scene_file, 'BEAM-DIMAP')
    print('Mask: done!')
    return coh_bands
    
    
    

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
    import os
    import sys
    import snappy
    from snappy import ProductIO, GPF, WKTReader
  
    
    base_dir =os.getcwd()
    try:
        os.chdir('data')
        scene_file = os.path.join(base_dir,'data',scene_name)
        print(scene_file)
        SAR_image = ProductIO.readProduct(scene_file)
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
        out_scene_file = os.path.join(base_dir,'preprocessed', scene_name[17:25]+'_subset')
        print(out_scene_file)
        ProductIO.writeProduct(SAR_image_subset, out_scene_file, 'BEAM-DIMAP')
        print('Done subsetting')
        os.chdir(base_dir)
    except Exception as e:
        sys.exit(e)
    finally:
        os.chdir(base_dir)
    
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
   
    # Check for new data
    lstd = read_environment()['latest']+":23:59"
    dt_latest = datetime.strptime(lstd, "%Y%m%d:%H:%M")
    scenes_df_new = scenes_df[(scenes_df['beginposition'])>dt_latest]


    if len(scenes_df_new)==0:
        print('No new data')
    else:
        # for a better error handling see
        # https://stackoverflow.com/questions/44893461/problems-exiting-from-python-using-ipython-spyder
        # and
        # https://sentinelsat.readthedocs.io/en/stable/api_reference.html#module-sentinelsat.exceptions
        if len(scenes_df_new)>1:
            print('There are  - ' + str(len(scenes_df_new)) + ' -  scenes to download')
        #print('Would like to download ', scenes_df_new.iloc[-1]['title'])
        
        for _,scn in scenes_df_new[::-1].iterrows():
            os.chdir('data')
        
            try:
                api.download(scn['uuid'])
                envd['latest'] = scn['title'][17:25]
                os.chdir(base_dir)
                write_environment(envd)
            except Exception as e:
                sys.exit(e)
            finally:
                os.chdir(base_dir)
        
                
            