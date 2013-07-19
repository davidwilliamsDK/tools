##########################publish##########################
dev = "dsDev"
live = "dsGlobal"
status = dev
server = '//vfx-data-server/'
##########################publish##########################


import re,os,sys,subprocess,shutil, fnmatch
sys.path.append(server + status + '/dsCore/maya/dsCommon/')

import dsOsUtil
import dsProjectUtil

import dsXML
import dsNukeVersionUp
import dsSubProcess

from PyQt4 import QtGui, QtCore, uic
if sys.platform == "linux2":
    uiFile = status + '/dsCore/tools/dsLauncher/dsLauncher.ui'
else:
    uiFile = server + status + '/dsCore/tools/dsLauncher/dsLauncher.ui'
print 'Loading ui file:', os.path.normpath(uiFile)
form_class, base_class = uic.loadUiType(uiFile)

class MyForm(base_class, form_class):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        super(base_class, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName('dsNukeTools')
        self.setWindowTitle("dsNukeTools")
        
        self.dsPipe = "//vfx-data-server/dsPipe/"  
        self.dsComp = '//xserv2/VFXSAN/dsComp/'
        
        self.dsProjectList = []
        self.getProjectList('ALL')
        
        self.dsPrj = ""
        self.dsepisode = ""
        self.seqList = []
        self.shotList = []
        
        QtCore.QObject.connect(self.projectCB, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateEpi)
        QtCore.QObject.connect(self.episodeCB, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateSeq)
        QtCore.QObject.connect(self.seqLV, QtCore.SIGNAL("itemSelectionChanged()"), self.updateShot)
        QtCore.QObject.connect(self.shotLV, QtCore.SIGNAL("itemSelectionChanged()"), self.getShotInfo)
        QtCore.QObject.connect(self.action_SA, QtCore.SIGNAL("triggered()"), self.showAll)
        QtCore.QObject.connect(self.action_SL, QtCore.SIGNAL("triggered()"), self.showLEGO)
        QtCore.QObject.connect(self.action_SC, QtCore.SIGNAL("triggered()"), self.showCommercial)
        QtCore.QObject.connect(self.actionUpdateRL, QtCore.SIGNAL("triggered()"), self.findNewRL)
        QtCore.QObject.connect(self.actionResubmitUp, QtCore.SIGNAL("triggered()"), self.nukeScriptVersionUp)
        QtCore.QObject.connect(self.actionHistoryRL, QtCore.SIGNAL("triggered()"), self.historyRL)
        QtCore.QObject.connect(self.actionBackUp, QtCore.SIGNAL("triggered()"), self.backup)
        QtCore.QObject.connect(self.actionBackUp, QtCore.SIGNAL("triggered()"), self.backup)
        QtCore.QObject.connect(self.maya_PB, QtCore.SIGNAL("clicked()"), self.launchMaya)
        QtCore.QObject.connect(self.nuke_PB, QtCore.SIGNAL("clicked()"), self.launchNuke)
        QtCore.QObject.connect(self.maya_CB, QtCore.SIGNAL("clicked()"), self.updatefileTW)
        QtCore.QObject.connect(self.nuke_CB, QtCore.SIGNAL("clicked()"), self.updatefileTW)


    def getShotInfo(self):
        self.getShotList()
        self.updatefileTW()
        
    def updatefileTW(self):
        if self.seqLV.currentRow() > -1:
            #print self.seqLV.currentRow()
            if self.shotLV.currentRow() > -1:
                seqItem = self.shotLV.currentItem()
                seq = seqItem.text()
                self.getProjPath()
                self.fileTW.clear()
                if self.nuke_CB.checkState() == 2:
                    print "load nuke stuff"
                    self.fileTW.setColumnCount(1)
                    for shot in self.getShotList():
                        temp = QtGui.QTreeWidgetItem()
                        temp.setText(0,str(shot))
                        self.getLatestNS(shot)
                        x = 1
                        for ns in self.nukeList:
                            tmp = QtGui.QTreeWidgetItem()
                            tmp.setText(0,str(ns))
                            tmp.setText(1,str(seq))
                            tmp.setText(2,str(shot))
                            temp.addChild(tmp)
                            #temp.setText(x,str(ns))
                            x += 1
                        self.fileTW.addTopLevelItem(temp)
                
                if self.maya_CB.checkState() == 2:
                    print "load maya stuff"
                    self.fileTW.setColumnCount(1)
                    for shot in self.getShotList():
                        temp = QtGui.QTreeWidgetItem()
                        temp.setText(0,str(shot))
                        seq = self.seqLV.currentItem().text()
                        mayaSceneList = self.getMayaScenes(seq, shot)                
                        #mayaSceneList_tmp = self.getMayaScenes(seq, shot)
                        #mayaSceneList = mayaSceneList_tmp.split()
                        x = 1
                        for m in mayaSceneList:
                            tmp = QtGui.QTreeWidgetItem()
                            tmp.setText(0,str(m))
                            tmp.setText(1,str(shot))
                            temp.addChild(tmp)
                            #temp.setText(x,str(ns))
                            x += 1
                        self.fileTW.addTopLevelItem(temp)

    def getMayaScenes(self,seq,shot):
        print "----maya scenes stuff----"
        mList = []
        animSubFolders = dsProjectUtil.animPathList()
        path = ""

        if re.search("LEGO",self.dsPrj):
            path = dsProjectUtil.seqAnimPath(self.dsPrj, self.episode, seq)
        else:
            path = dsProjectUtil.shotAnimPath(self.dsPrj, self.episode, seq, shot)
        
        if animSubFolders:
            if path:
                for animSub in animSubFolders:
                    tmpList = os.listdir(path + animSub)
                    for file in tmpList:
                        if file[-3:] == ".ma" or file[-3:] == ".mb":
                            mList.append(file)

        return mList
        
    #===========================================================================
    # def updateMayaBasePath(self,seq,shot):
    #    filmList = ("/Film","/film")
    #    for film in filmList:
    #        if os.path.isdir(self.projPath + film):
    #            basePath = self.projPath + film + "/" + self.episode + "/" + self.seqList[0] + "/" + shot 
    #    searchList = ("scenes","anim","blocking","light","effect","_Anim","_Blocking","_Light","_Effect")
    #    cfiles = []
    #    for dirs in os.walk(str(basePath)):
    #        for folder in searchList:
    #            if re.search(str(folder),str(dirs)):
    #                cfiles.append(dirs[0])
    #                break
    #    return cfiles
    #===========================================================================

         
    def testFile(self):
        if self.seqLV.currentRow() > -1:
            item = self.seqLV.currentItem()
            self.seq = item.text()
            #print self.seqLV.currentRow()
            if self.shotLV.currentRow() > -1:
                #print self.shotLV.currentRow()
                if self.fileTW.currentItem() != None:
                    item = self.fileTW.currentItem()
                    self.seq = item.text(1)
                    self.shot = item.text(2)
                    if self.nuke_CB.checkState() == 2:
                        nkPath = self.updateNukeBasePath(self.shot) + "/" + item.text(0)
                        return nkPath
                    #if self.maya_CB.checkState() == 2:
                        #msPath = self.updateMayaBasePath(self.shot) + "/" + item.text(0)
                        #return msPath

    def launchNuke(self):
        ''' global env'''
        os.environ['NUKE_PATH'] = '//framestore/pipeline/pantry/globalNuke'
        os.environ['NUKE_PLUGINS_PATH'] = '//framestore/pipeline/pantry/globalNuke/'
        os.environ['NUKE_GIZMO_PATH'] = '//framestore/pipeline/pantry/globalNuke/gizmos/'
        os.environ['NUKE_PYTHON_PATH'] = '//framestore/pipeline/pantry/globalNuke/python'
        os.environ['OFX_PLUGIN_PATH'] = '//framestore/pipeline/pantry/globalNuke/plugins/OFX/win64'
        
        file = self.testFile()
        
        ''' script env '''
        os.environ['RELATIVEPATH'] = "//vfx-data-server/"
        os.environ['PROJECT'] = str(self.dsPrj)
        os.environ['EPISODE'] = str(self.episode)
        os.environ['SEQUENCE'] = str(self.seq)
        os.environ['SHOT'] = str(self.shot)
        
        cmd = 'C:/Program Files/Nuke6.3v7/Nuke6.3.exe' + ' ' +  str(file)
        dsSubProcess.dsProcess(str(cmd))
        print "start NUKE"


    def launchMaya(self):
        ''' global env '''
        os.environ['PYTHONPATH'] = '//vfx-data-server/dsDev/dsCore/maya;//vfx-data-server/dsDev/globalMaya/Resources/2011/PyQt_Win64;'
        os.environ['MAYA_SCRIPT_PATH'] ='//vfx-data-server/dsDev/globalMaya/Mel'
        file = self.testFile()
        
        ''' scene env '''
        os.environ['RELATIVEPATH'] = "//vfx-data-server/"
        os.environ['PROJECT'] = str(self.dsPrj)
        os.environ['EPISODE'] = str(self.episode)
        os.environ['SEQUENCE'] = str(self.seq)
        os.environ['SHOT'] = str(self.shot)
        os.environ['MAYA_PROJECTS_DIR'] = str(file)
        cmd = 'C:/Program Files/Autodesk/Maya2012/bin/maya.exe'
        #print str(cmd) + ' ' + str(file)
        dsSubProcess.dsProcess(str(cmd) + ' ' + str(file))
        print "start maya"

    def backup(self):
        print 'backing up'
        self.getProjPath()
        shotList = self.defineShots()
        
        nRLList =  []
        for shot in shotList:
            nPath = self.getLatestNS(shot)
            if not nPath == None:
                ns = dsNukeVersionUp.dsNukeVersionUp(str(nPath),"backUp")

    def historyRL(self):
        ''' run create history of RenderLayers on selected shots.'''
        self.getProjPath()
        shotList = self.defineShots()
        
        for shot in self.shotList:
            nPath = self.getLatestNS(shot)
            ns = dsNukeVersionUp.dsNukeVersionUp(str(nPath),"history")

    def findNewRL(self):
        ''' find New RenderLayers on selected seq.'''
        self.shotLV.setCurrentRow(-1)
        self.getProjPath()
        shotList = self.defineShots()
        
        nRLList =  []
        for shot in shotList:
            nPath = self.getLatestNS(shot)
            if not nPath == None:
                ns = dsNukeVersionUp.dsNukeVersionUp(str(nPath),"find")
                if ns.checkReads() == True:
                    nRLList.append(shot)
        self.updateRLList(nRLList)

    def nukeScriptVersionUp(self):
        ''' Version up and sumbit to farm nuke Script with latest version of Renderlayer.'''
        self.getProjPath()
        for shot in self.shotList:
            nPath = self.getLatestNS(shot)
            ns = dsNukeVersionUp.dsNukeVersionUp(str(nPath),"reSub")

    def defineShots(self):
        
        if not os.path.isdir(self.dsComp + self.dsPrj):
            projPath = self.dsPipe + self.dsPrj
        else:
            projPath = self.dsComp + self.dsPrj
        shotList = []
        shotListTmp = os.listdir(projPath + "/Film/" + self.episode + "/" + self.seqList[0])
        for shot in shotListTmp:
            if re.match ("(s[0-9][0-9][0-9][0-9])",shot) or re.match("(S[0-9][0-9][0-9][0-9])",shot):
                shotList.append(shot)
        shotList.sort()
        return shotList

    def getProjPath(self):
        self.projPath = ""
        if self.nuke_CB.checkState() == 2:
            if not os.path.isdir(self.dsComp + self.dsPrj):
                self.projPath = self.dsPipe + self.dsPrj
            else:
                self.projPath = self.dsComp + self.dsPrj
        if self.maya_CB.checkState() == 2:
            self.projPath = self.dsPipe + self.dsPrj
                    
    def getLatestNS(self,shot):
            basePath = self.updateNukeBasePath(shot)
            nsList = []
            nsVerList = []
            self.nukeList = []
            nukeDirList = os.listdir(basePath)
            for ns in nukeDirList:
                if re.search('.nk',ns):
                    if not re.search('autosave',ns):
                        if not re.search('~',ns):
                            if re.search('v\d{3}',ns):
                                self.nukeList.append(ns)
                                nsVer = re.search('v\d{3}',ns).group()
                                nsVerList.append(nsVer)
            nsVerList.sort()
            if not self.nukeList == []:
                for ns in self.nukeList:
                    if re.search(shot,ns):
                        if re.search(nsVerList[-1],ns):
                            nPath = basePath + "/" + ns
                            return nPath

    def updateNukeBasePath(self,shot):
        if os.path.isdir(self.projPath + "/Film"):
            basePath = self.projPath + "/Film/" + self.episode + "/" + self.seqList[0] + "/" + shot
        elif os.path.isdir(self.projPath + "/film"):
            basePath = self.projPath + "/film/" + self.episode + "/" + self.seqList[0] + "/" + shot
            
        if os.path.isdir(basePath + "/comp"):
            basePath = basePath + "/comp"
        elif os.path.isdir(basePath + "/Comp"):
            basePath = basePath + "/Comp"
            
        if os.path.isdir(basePath + "/nukeScripts"):
            basePath = basePath + "/nukeScripts"
        elif os.path.isdir(basePath + "/nukeScript"):
            basePath = basePath + "/nukeScript"
        elif os.path.isdir(basePath + "/2dScript"):
            basePath = basePath + "/2dScript"
        return basePath
    
    def updateRLList(self,nRLList):
        for rl in nRLList:
            item = self.shotLV.findItems(rl, QtCore.Qt.MatchRegExp)
            self.shotLV.setItemSelected (item[0],True)
             
    def getSeqList(self):
        self.seqList=[]
        items = self.seqLV.selectedItems()
        for i in range(len(items)):
            self.seqList.append(str(self.seqLV.selectedItems()[i].text()))
        return self.seqList
        
    def getShotList(self):
        self.shotList=[]
        items = self.shotLV.selectedItems()
        for i in range(len(items)):
            self.shotList.append(str(self.shotLV.selectedItems()[i].text()))  
        return self.shotList
    
    def getProjectList(self,dept):
        ''' Updates gui bye folder searching'''
        self.dsProjectList = dsXML.scanXML(self.dsPipe,dept)
        self.projectCB.clear()
        self.dsProjectList.sort()
        for project in self.dsProjectList:
            self.projectCB.addItem(project)
            
    def updateEpi(self):
        ''' Updates gui bye folder searching'''
        self.dsPrj = self.projectCB.currentText()
        epiList = os.listdir(self.dsPipe + self.dsPrj + "/Film/")
        epiList.sort()
        self.episodeCB.clear()
        for epi in epiList:
            if os.path.isdir(self.dsPipe + self.dsPrj + "/Film/" + epi):
                if not epi.startswith('.'):
                    self.episodeCB.addItem(epi)
                
    def updateSeq(self):
        ''' Updates gui bye folder searching'''
        self.seqLV.clear()
        data = self.episodeCB.currentText()
        seqList = os.listdir(self.dsPipe + self.dsPrj + "/Film/" + str(data) + "/")
        seqList.sort()
        for seq in seqList:
            if re.match("(Q[0-9][0-9][0-9][0-9])",seq) or re.match("(q[0-9][0-9][0-9][0-9])",seq):
                self.seqLV.addItem(seq)
        
    def updateShot(self):
        ''' Updates gui bye folder searching'''
        self.getSeqList()
        self.shotLV.clear()
        
        self.episode = self.episodeCB.currentText()
        tmpList = []
        for seq in self.seqList:
            shotList = os.listdir(self.dsPipe + self.dsPrj + "/Film/" + str(self.episode) + "/" + str(seq) + "/")
            shotList.sort()
            for shot in shotList:
                if re.match("(S[0-9][0-9][0-9][0-9])",shot) or re.match ("(s[0-9][0-9][0-9][0-9])",shot):
                    if shot not in tmpList:
                        tmpList.append(shot)
        for shot in tmpList:
            self.shotLV.addItem(shot)

    def showAll(self):
        ''' Updates gui drop down to show ALL jobs'''
        self.action_SA.setChecked(2)
        self.action_SL.setChecked(0)
        self.action_SC.setChecked(0)
        self.getProjectList("ALL")
        
    def showLEGO(self):
        ''' Updates gui drop down to show only Lego jobs'''
        self.action_SA.setChecked(0)
        self.action_SL.setChecked(2)
        self.action_SC.setChecked(0)
        self.getProjectList("LEGO")
        
    def showCommercial(self):
        ''' Updates gui drop down to show only commercial jobs'''
        self.action_SA.setChecked(0)
        self.action_SL.setChecked(0)
        self.action_SC.setChecked(2)
        self.getProjectList("Commercial")
                   
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
    