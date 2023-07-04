# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import snappy
from snappy import ProductIO, GPF


def listParams(operator_name):
    #https://forum.step.esa.int/t/where-to-find-operator-parameters-for-snappy/4621/7
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    op_spi = GPF.getDefaultInstance().getOperatorSpiRegistry().getOperatorSpi(operator_name)
    print('Op name:', op_spi.getOperatorDescriptor().getName())
    print('Op alias:', op_spi.getOperatorDescriptor().getAlias())
    print('PARAMETERS:\n')
    param_Desc = op_spi.getOperatorDescriptor().getParameterDescriptors()
    for param in param_Desc:
        print('{}: {}\nDefault Value: {}\n'.format(param.getName(),param.getDescription(),param.getDefaultValue()))

listParams("Collocate")

def get_all_operators():
    #https://forum.step.esa.int/t/where-to-find-operator-parameters-for-snappy/4621/7
    op_spi_it = GPF.getDefaultInstance().getOperatorSpiRegistry().getOperatorSpis().iterator()
    while op_spi_it.hasNext():
        op_spi = op_spi_it.next()
        print("op_spi: ", op_spi.getOperatorAlias())

#get_all_operators()
#Calibration
#Speckle-Filter
#Terrain-Corection
#Apply-Orbit-File
#Subset
#Resample
#Read
#TOPSAR-Deburst
#TOPSAR-Split

#list https://seadas.gsfc.nasa.gov/help-8.3.0/gpf/GraphProcessingTool.html 
#more https://snap-contrib.github.io/snapista/examples/graph.html
