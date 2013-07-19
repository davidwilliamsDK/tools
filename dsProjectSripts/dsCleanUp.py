'''
Created on 09/11/2012

@author: David
'''
import os,re,shutil


def clearPath(path):
    print path
    shutil.rmtree(path)

def getPaths(rootPath):
    dsComp = "//xserv2.duckling.dk/dsComp"
    dsPipe = "//vfx-data-server/dsPipe"
    dsPipePath = dsPipe + "/" + path 
    dsCompPath = dsComp + "/" + path
    
    killList=['incrementalSave','versions','Version','Versions','version','History','history','_history','_History','old','_old','Old']
    #killList=['incrementalSave','History','history','_history','_History','old','_old','Old']
    #srvList = [dsPipePath,dsCompPath]
    srvList = [dsPipePath]    
    
    for srvPath in srvList:
        print srvPath
        for dir, subdirs, files in os.walk(srvPath):
            for d in subdirs:
                if d in killList:
                    clearPath(os.path.join(dir, d))

rootPath = "//vfx-data-server/dsPipe/"
project = "Lego_City"
projPath = project + "/film/"
epiList = os.listdir(rootPath + projPath)

for epi in epiList:
    path = projPath + epi
    #path = "Lego_Chima/film/2012_FALL_CrocLion_010295"
    print path
    getPaths(path)