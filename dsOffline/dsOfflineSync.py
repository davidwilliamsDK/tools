'''
Created on Aug 28, 2012

@author: David
'''
from xml.etree import ElementTree as ET
from xml.dom import minidom
import sys, os, re, shutil, imp

if sys.platform == "linux2":
    uiFile = '/mounts/vfxstorage/dsDev/dsCore/tools/dsOffline/dsOfflineSync.ui'
    sys.path.append('/mounts/vfxstorage/dsGlobal/dsCore/maya/dsCommon/')
    sys.path.append('/mounts/vfxstorage/dsGlobal/dsCore/shotgun/')
    
else:
    uiFile = '//vfx-data-server/dsDev/dsCore/tools/dsOffline/dsOfflineSync.ui'
    sys.path.append('//vfx-data-server/dsGlobal/dsCore/maya/dsCommon/')
    sys.path.append('//vfx-data-server/dsGlobal/dsCore/shotgun/')

from PyQt4 import QtGui, QtCore, uic
import sgTools;reload(sgTools)

print 'Loading ui file:', os.path.normpath(uiFile)
form_class, base_class = uic.loadUiType(uiFile)

class MyForm(base_class, form_class):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        super(base_class, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName('dsProjectCreate')
        self.setWindowTitle("dsProjectCreate")
        
        if sys.platform == "linux2":
            self.dsPipe = "/dsPipe/"
        else:
            self.dsPipe = "//vfx-data-server/dsPipe/"
            
            
            
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())