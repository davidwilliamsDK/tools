import re,os,sys,itertools
from subprocess import Popen, PIPE, STDOUT

from PyQt4 import QtGui, QtCore, uic

#sys.path.append('../Shotgun')
from shotgun_api3 import Shotgun
import dsEDL


### os path conversions ###
if sys.platform == "darwin":
    uiFile = '/Users/m2film/Dropbox/EDL/EDLTools.ui'   
if sys.platform == "linux2":
    uiFile = '/Users/m2film/Desktop/EDL/EDLTools.ui'   
if sys.platform == "win32":
    sys.path.append('//vfx-data-server/dsGlobal/dsCore/shotgun/')
    sys.path.append('//vfx-data-server/dsGlobal/dsCore/maya/dsCommon/')
    uiFile = 'U:/dsCore/tools/EDL/EDLTools.ui'

import sgTools;reload(sgTools)
import dsFolderStruct as dsFS

print 'Loading ui file:', os.path.normpath(uiFile)
form_class, base_class = uic.loadUiType(uiFile)

class MyForm(base_class, form_class):

    def __init__(self, parent=None):       
        if sys.platform == "darwin":
            self.ffMpeg = '/Users/m2film/Dropbox/EDL/ffmpeg/mac/ffmpeg'
        if sys.platform == "linux2":
            self.ffMpeg = '/Users/m2film/Dropbox/EDL/ffmpeg/mac/ffmpeg'
        if sys.platform == "win32":
            self.rvIO = '"C:\\Program Files (x86)\\Tweak\\RV-3.12.20-32\\bin\\rvio.exe"'
            self.ffMpeg = 'U:/dsCore/tools/EDL/ffmpeg/win/bin/ffmpeg.exe'
        QtGui.QWidget.__init__(self, parent)
        super(base_class, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName('EDLTools')
        self.setWindowTitle("EDLTools")
        
        ### button connections 
        self.cb_shotgunServer.currentIndexChanged.connect(self.updateProj)
        self.cb_Project.currentIndexChanged.connect(self.updateEpi)
        self.pb_loadEDL.clicked.connect(self.loadEDL)
        self.pb_loadQT.clicked.connect(self.loadQT)
        self.pb_preview.clicked.connect(self.preview)
        self.pb_create.clicked.connect(self.epiCutup)
        
    def epiCutup(self):
        qtIn = str(self.le_pathQT.text())
        pathSplit = qtIn.split("/")
        basePath = qtIn.replace(pathSplit[-1],"")
        basePath = basePath + "media"
        if not os.path.isdir(basePath):os.mkdir(basePath)
        
        for x in sorted(self.epiDict):
            for y in sorted(self.epiDict[x]):
                shotName = y.replace(self.epiKey,"")
                
                tcIn = dsEDL.TCtoFrames(self.epiDict[x][y]['tcIn'],int(self.FPS))
                tcOut = dsEDL.TCtoFrames(self.epiDict[x][y]['tcOut'],int(self.FPS))

                shotDur = dsEDL.frames_to_msTC(int(self.FPS),int(self.epiDict[x][y]['durFrames']))
                qtOut = basePath + "/" + shotName + ".mov"
                
                jpgOut = basePath + "/" + shotName + ".jpg"

                self.qtSlice(qtIn,qtOut,tcIn,tcOut)
                self.qtThumb(qtIn,jpgOut,tcIn,tcOut)
                
                self.updateSG(shotName,qtOut,jpgOut,qtIn)
                
                ## create folder structures ##
                tmpVal =shotName.split("_")
                
                dsPipe = "//vfx-data-server/dsPipe/"
                dsComp = "//xserv2.duckling.dk/dsComp/"
                
                fullPath = dsPipe + str(self.cb_Project.currentText()) + "/film/"+ str(self.cb_Episode.currentText()) + "/"+ tmpVal[0]+"/"
                dsFS.dsCreateFs("3D",fullPath,tmpVal[-1])
                
                fullPath = dsComp + str(self.cb_Project.currentText()) + "/film/"+ str(self.cb_Episode.currentText()) + "/"+ tmpVal[0]+"/"
                dsFS.dsCreateFs("COMP",fullPath ,tmpVal[-1])
    
    
    def updateSG(self,shotName,qtOut,jpgOut,qtIn):
        projName = str(self.cb_Project.currentText())
        epiName = str(self.cb_Episode.currentText())
        
        keyName = shotName
        shotSplit = shotName.split("_")
        seqName = shotSplit[0]
        shotName = shotSplit[-1]

        myProj = sgTools.sgGetProject(projName,[])
        myEpi = sgTools.sgGetEpisode(epiName,projName,[])
        mySeq = sgTools.sgGetSequence(seqName,projName,epiName,['code','id'])
        myShot = sgTools.sgGetShot(self.sg,shotName,seqName,projName,epiName,['code','id'])
        
        start = self.epiDict[seqName][keyName]['seqStart']
        end = self.epiDict[seqName][keyName]['seqEnd']
        dur = int(self.epiDict[seqName][keyName]['durFrames']) + 1
        
        qtIn = qtIn.replace("P:/","dsPipe/")
        qtOut = qtOut.replace("P:/","dsPipe/")
        qtIn = qtIn.replace("S:/","dsComp/")
        qtOut = qtOut.replace("S:/","dsComp/")

        ## create and or update Sequences with quicktime
        if self.sg.find_one("Sequence", [['code','is', seqName], ['project.Project.name','is', str(projName)],['scene_sg_sequence_1_scenes.Scene.code','is', str(epiName)]],['code']) == None:
            filters = [ ['code','is', 'DucklingSequenceTemplate' ]]
            template = self.sg.find_one('TaskTemplate',filters)
            
            data = { 'project':myProj,'code': seqName,'scene_sg_sequence_1_scenes':[myEpi,],'image':str(jpgOut),'sg_path_to_edit':qtIn,'sg_sequence_type':'Sequence','task_template': template}
            result = self.sg.create('Sequence', data)
            try:self.te_log.appendPlainText( "created " + str(mySeq['code']) + " in shotGun")
            except:pass
        else:
            self.sg.update('Sequence',mySeq['id'], {'image':str(jpgOut)})
            try:self.te_log.appendPlainText( "updated " + str(mySeq['code']) + " in shotGun")
            except:pass
            
        ## create and or update Shots with quicktime
        '''
        if self.sg.find_one("Shot", [['code','is', shotName], ['project.Project.name','is', str(projName)],['sg_sequence.Sequence.code','is', str(seqName)],['sg_scene.Scene.code','is', str(epiName)]],[]) == None:
            filters = [ ['code','is', 'DucklingShotTemplate' ]]
            template = self.sg.find_one('TaskTemplate',filters)

            data = {'code':shotName,'sg_sequence':mySeq,'image':str(jpgOut),'sg_scene':myEpi,'project':myProj,'sg_path_to_movie':str(qtOut),'task_template': template,'sg_cut_in':start,'sg_cut_out':end,'sg_cut_duration':dur}
            result = self.sg.create('Shot', data)
            
            try:self.te_log.appendPlainText("created shot in shotgun")
            except:pass
        else:
            self.sg.update('Shot',myShot['id'], {'sg_cut_in':start,'sg_cut_out':end,'sg_path_to_movie':str(qtOut),'sg_cut_duration':dur,'image':str(jpgOut)})
            
            try:self.te_log.appendPlainText( "updated " + str(myShot['code']) + " in shotGun")
            except:pass
        ''' 
            
        ## create and or update Version with quicktime
        if self.sg.find_one("Version", [['code','is', shotName + "_aimatic"], ['project.Project.name','is', str(projName)],['entity.Shot.code','is', str(shotName)],['sg_sequence.Sequence.code','is', str(seqName)],['sg_scene.Scene.code','is', str(epiName)]],[]) == None:
            filters = [ ['code','is', 'DucklingShotTemplate' ]]
            template = self.sg.find_one('TaskTemplate',filters)

            data = {'code':shotName + "_aimatic",'sg_sequence':mySeq,'image':str(jpgOut),'sg_scene':myEpi,'project':myProj,'entity':myShot,'sg_path_to_movie':str(qtOut),'task_template': template,'sg_cut_in':start,'sg_cut_out':end,'sg_cut_duration':dur}
            result = self.sg.create('Shot', data)
            
            try:self.te_log.appendPlainText("created shot in shotgun")
            except:pass
        else:
            self.sg.update('Version',myShot['id'], {'sg_cut_in':start,'sg_cut_out':end,'sg_path_to_movie':str(qtOut),'sg_cut_duration':dur,'image':str(jpgOut)})
            
            try:self.te_log.appendPlainText( "updated " + str(myShot['code']) + " in shotGun")
            except:pass
            
            
            
    def adjustTC(self,tc,offset):
        tcSplit = tc.split(":")
        offSS = offset.split(":")

        HH = int(tcSplit[0]) - int(offSS[0])
        MM = int(tcSplit[1]) - int(offSS[1])
        return '%02d:%02d:%s' % (HH,MM,tcSplit[2])

    def qtThumb(self,qtIn,jpgOut,tcIn,tcOut):
        # Create Icon 
        tcIn = tcIn + 1
        cmd = self.rvIO + " " + str(qtIn) + " -t " + str(tcIn) + " -o " + jpgOut
        
        process = os.popen(cmd)
        self.te_log.appendPlainText("icon for "+jpgOut+" created.")
    
    def qtSlice(self,qtIn,qtOut,tcIn,tcOut):
        #RUNS rvIO command line too cut up qt into timecode start and duration
        tcIn = tcIn + 1
        cmd = self.rvIO + " " + str(qtIn) + " -t " + str(tcIn) + "-" + str(tcOut) + " -o " + qtOut

        process = os.popen(cmd)
        self.te_log.appendPlainText(cmd)
        self.te_log.appendPlainText("QT for "+qtOut+" created.")

    def preview(self):
        
        try:
            previewName = dsEDL.getSource(self.edlFile)
            
            self.le_preview.setText(previewName)
            self.epiKey = str(self.le_epiKey.text())
            self.seqKey = str(self.le_sqKey.text())
            self.shotKey = str(self.le_shKey.text())
            self.tcOffset = str(self.le_tcOffset.text())
            self.FPS = int(self.le_FPS.text())
            
            seqKey = self.seqKey.replace("#","[0-9]")
            shotKey = self.shotKey.replace("#","[0-9]")
            
            self.le_epiPreview.setText(re.search(str(self.epiKey),str(previewName)).group())
            self.le_seqPreview.setText(re.search(str(seqKey),str(previewName)).group())
            self.le_shotPreview.setText(re.search(str(shotKey),str(previewName)).group())
            
            self.projKey = str(self.cb_Episode.currentText())            
            self.epiKey = str(self.le_epiKey.text())
            self.seqKey = str(self.le_sqKey.text())
            self.shotKey = str(self.le_shKey.text())
            
            self.te_log.appendPlainText("server: " + self.cb_shotgunServer.currentText())
            self.te_log.appendPlainText("project: " + self.cb_Project.currentText())
            self.te_log.appendPlainText("episode: " + self.cb_Episode.currentText())
            self.te_log.appendPlainText("######READY TO GO######")
            
            self.getSeqShots()
            
        except:
            pass
                
    def getSeqShots(self):

        rowCount = self.tw_sqsh.rowCount()
        if rowCount > 0:
            self.clearTW()
        
        self.le_pathEDL = str(self.edlFile)
        self.te_log.appendPlainText(self.edlFile)
        
        self.epiDict = dsEDL.readEDL(self.edlFile,self.seqKey,self.shotKey,self.FPS)
        
        tmpList = []

        for x in sorted(self.epiDict):
            for y in sorted(self.epiDict[x]):
                
                self.tw_sqsh.insertRow(rowCount)
                
                shotName = y.replace(self.epiKey,"")
                item = QtGui.QTableWidgetItem(shotName)
                self.tw_sqsh.setItem(rowCount,0,item)

                shotStart = str(self.epiDict[x][y]['tcIn'])
                item = QtGui.QTableWidgetItem(shotStart)
                self.tw_sqsh.setItem(rowCount,1,item)
                
                shotEnd = str(self.epiDict[x][y]['tcOut'])
                item = QtGui.QTableWidgetItem(shotEnd)
                self.tw_sqsh.setItem(rowCount,2,item)

                try:
                    seqStart = str(self.epiDict[x][y]['seqStart'])
                    tItem = QtGui.QTableWidgetItem(seqStart)
                    self.tw_sqsh.setItem(rowCount,3,tItem)
                except:
                    shotStart = str(self.epiDict[x][y]['shotStart'])
                    item = QtGui.QTableWidgetItem(shotStart)
                    self.tw_sqsh.setItem(rowCount,3,item)
                try:
                    seqEnd = str(self.epiDict[x][y]['seqEnd'])
                    tItem = QtGui.QTableWidgetItem(seqEnd)
                    self.tw_sqsh.setItem(rowCount,4,tItem)
                except:
                    shotEnd = str(self.epiDict[x][y]['shotEnd'])
                    item = QtGui.QTableWidgetItem(shotEnd)
                    self.tw_sqsh.setItem(rowCount,4,item)
                
                shotDur = str(self.epiDict[x][y]['shotDur'])
                item = QtGui.QTableWidgetItem(shotDur)
                self.tw_sqsh.setItem(rowCount,5,item)
                
                rowCount = rowCount + 1

    def shotgunServer(self):
        server = "https://duckling.shotgunstudio.com"
        scriptName = "EDLTools"
        scriptId = "420488d04ac10613f07fd00d1eff5c0217a6f75e"
        self.sg = Shotgun(server, scriptName, scriptId)
        sServer = self.cb_shotgunServer.currentText()
        
    def updateProj(self):
        
        self.cb_Project.setEnabled(True)
        self.cb_Episode.setEnabled(False)
        self.cb_Project.clear()
        self.getProjList()

    def updateEpi(self):
        
        self.cb_Episode.setEnabled(True)
        self.cb_Episode.clear()
        self.getEpiList()
           
    def getProjList(self):
        #test and load projects into GUI
        self.shotgunServer()
        self.projList = self.sg.find("Project", [["sg_status", "is", "Active"]], ['name'])
        self.cb_Project.clear()
        self.cb_Project.addItem('-Select Project-')
        for proj in self.projList:
            self.cb_Project.addItem(proj['name'])
    
    def getEpiList(self):
        #test and load Episodes into GUI
        self.shotgunServer()
        pProj = self.cb_Project.currentText()
        self.epiList = self.sg.find("Scene", [['project.Project.name','is', str(pProj)]], ['code'])
        self.cb_Episode.addItem('-Select Episode-')
        for epi in self.epiList:
            self.cb_Episode.addItem(epi['code'])
    
    def clearTW(self):
        rowCount = self.tw_sqsh.rowCount()
        
        while i <= rowCount:
            self.tw_sqsh.removeRow(i)
            i = i -1
                    
    def loadEDL(self):
        #load edl file
        self.edlFile = QtGui.QFileDialog.getOpenFileName(self, "Open Data File", "", "EDL (*.edl)")
        self.le_pathEDL.setText(self.edlFile)
        
    def loadQT(self):
        #load qt file
        self.qtFile = QtGui.QFileDialog.getOpenFileName(self, "Open Data File", "", "Quicktime MOV ()")
        self.le_pathQT.setText(self.qtFile)
            
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())