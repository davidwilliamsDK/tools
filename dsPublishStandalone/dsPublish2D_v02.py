print 'v1.0.5'

import sys, os, glob, time, re, shutil, subprocess, hashlib, random

if sys.platform == 'linux2':
    sys.path.append('/dsGlobal/globalMaya/Python/PyQt_Linx64')
    sys.path.append('/dsGlobal/dsCore/shotgun')
    sys.path.append('/dsGlobal/dsCore/maya/dsCommon')
    from PyQt4 import QtGui, QtCore, uic
    form_class, base_class = uic.loadUiType("/dsGlobal/dsCore/tools/dsPublishStandalone/dsPublish2D.ui")
else:
    sys.path.append(r'\\vfx-data-server\dsGlobal\globalMaya\Python\PyQt_Win64')
    sys.path.append(r'\\vfx-data-server\dsGlobal\dsCore\shotgun')
    sys.path.append(r'\\vfx-data-server\dsGlobal\dsCore\maya\dsCommon')
    from PyQt4 import QtGui, QtCore, uic
    form_class, base_class = uic.loadUiType(r"\\vfx-data-server\dsGlobal\dsCore\tools\dsPublishStandalone\dsPublish2D.ui")
    
import sgTools, dsFilmCheck,dsCollect
import dsSubProcess as dsSP

from PIL import Image

class publishStandalone(form_class, base_class):
    '''
    Standalone tool for publishing frame stacks.
    Config file location user/config.ini
    '''
    def __init__(self, parent=None):
        base_class.__init__(self, parent)
        self.setupUi(self)
        self.publish_B.setEnabled(False)
        self.default_viewer = None

        if sys.platform == "linux2":
            self.dsPipe = '/dsPipe'
            self.dsComp = '/dsComp'
            self.home = os.getenv("HOME")
            self.config_dir = '%s/.publishNuke' % (self.home)
            self.config_path = '%s/config.ini' % (self.config_dir)
            self.rvRoot = "'/usr/local/rv-Linux-x86-64-3.20.15'"
            self.rvio = self.rvRoot + "'/bin/rvio'"
            self.rv = self.rvRoot + "'/bin/rv'"
            self.rvpush = self.rvRoot + "'/bin/rvpush'"
            self.rrCopy = "/rrender/bin/lin/rrCopy"
            self.rvplugs = "/dsGlobal/dsCore/rv/"
        elif sys.platform == 'win32':
            self.dsPipe = '//vfx-data-server/dsPipe'
            self.dsComp = 'S:'
            self.home = 'C:%s' % os.getenv("HOMEPATH")
            self.config_dir = '%s/.publishNuke' % (self.home)
            self.config_dir = self.config_dir.replace("/","\\")
            self.config_path = '%s/config.ini' % (self.config_dir)
            self.config_path = self.config_path.replace("/","\\")
            self.rvRoot = '"C:/Program Files (x86)/Tweak/RV-3.12.20-32"'
            self.rvio = self.rvRoot + '"/bin/rvio.exe"'
            self.rv = self.rvRoot + '"/bin/rv.exe"'
            self.rvpush = self.rvRoot + '"/bin/rvpush.exe"'
            self.rrCopy = "//vfx-render-server/royalrender/bin/win/rrCopy.exe"
            self.rvplugs = "//vfx-data-server/dsGlobal/globalRV/plugins/Mu"
            
        try:self.updateRVPlugs()
        except:pass
        
        self.refresh()

        self.projects_CB.currentIndexChanged.connect(self.init_episodes)
        self.episodes_CB.currentIndexChanged.connect(self.init_sequences)
        self.sequences_LW.itemSelectionChanged.connect(self.init_shots)
        self.sequences_LW.itemDoubleClicked.connect(self.open_sequences)
        self.shots_LW.itemSelectionChanged.connect(self.init_compOut)
        self.shots_LW.itemSelectionChanged.connect(self.init_nukeScripts)
        self.shots_LW.itemDoubleClicked.connect(self.open_shots)
        self.versionUp_B.clicked.connect(self.versionUp)
        self.compOut_LW.itemDoubleClicked.connect(self.open_compOut)
        self.compOut_LW.itemSelectionChanged.connect(self.check)
        self.nukeScripts_LW.itemDoubleClicked.connect(self.open_nukeScript)
        self.refresh_B.clicked.connect(self.save_config)
        self.updateThumb_B.clicked.connect(self.updateThumbs)
        self.openInRv_B.clicked.connect(self.openInRv)
        self.publishSeq_B.clicked.connect(self.publishSeq)
        self.updateOnline_B.clicked.connect(self.getLatestOnline)

        self.publish_B.clicked.connect(self.publish)
        self.GetUser()
        self.load_config()

    def getLatestOnline(self):
        print "getting latest version from shotgun"
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        sh = self.shots_LW.currentItem().text()
        version = sgTools.sgGetLatestOnline(pr,ep,sq,sh)
        if len(version) > 0:
            lv = version[-1]['code']
            self.compOut_LW
            items = [self.compOut_LW.item(i) for i in range(self.compOut_LW.count())]
            for i in items:
                if str(lv) == i.text():
                    i.setBackground(QtGui.QColor('green'))

    def openInRv(self):
        pr = str(self.projects_CB.currentText())
        ep = str(self.episodes_CB.currentText())
        sqList = self.sequences_LW.selectedItems()
        sq = sqList[0].text()
        rootSeq = '%s/%s/film/%s/%s/' % (self.dsComp, pr, ep, sq)

        if self.shots_LW.currentRow() >= 0 and self.compOut_LW.currentRow() >= 0:
            sh = str(self.shots_LW.currentItem().text())
            co = self.compOut_LW.currentItem().text()
            compOut= '%s/%s/film/%s/%s/%s/comp/compOut/%s/' % (self.dsComp, pr, ep, sq, sh,co)
            frameList = os.listdir(compOut)
            if frameList != []:
                frameList.sort()
                for frame in frameList:
                    if frame[-3:] == "exr" or frame[-3:] == "dpx":
                        nFrame = frame
                        break
                image = compOut + nFrame
                cmd = self.rvpush + ' merge %s' % (image)
                if sys.platform == "linux2":
                    self.process(cmd)
                else:
                    subprocess.Popen(cmd, creationflags = subprocess.CREATE_NEW_CONSOLE)

            print "open " + compOut + " framestack in RV"
        
        if self.shots_LW.currentRow() >= 0 and self.compOut_LW.currentRow() == -1:
            sh = str(self.shots_LW.currentItem().text())
            online= '%s/%s/film/%s/%s/%s/published2D/compOut/DPX/' % (self.dsComp, pr, ep, sq, sh)
            frameList = os.listdir(online)
            if frameList != []:
                frameList.sort()
                for frame in frameList:
                    if frame[-3:] == "exr" or frame[-3:] == "dpx":
                        nFrame = frame
                        break
                image = online + nFrame
                cmd = self.rvpush + ' merge %s' % (image)
                if sys.platform == "linux2":
                    self.process(cmd)
                else:
                    subprocess.Popen(cmd, creationflags = subprocess.CREATE_NEW_CONSOLE)

            print "open " + online + " framestack in RV"
        
        if self.shots_LW.currentRow() == -1 and self.compOut_LW.currentRow() == -1:
            dsCollect.parseLatest(rootSeq,"online")


    def updateThumbs(self):
        pr = str(self.projects_CB.currentText())
        ep = str(self.episodes_CB.currentText())
        sq = str(self.sequences_LW.currentItem().text())
        try:
            sh = str(self.shots_LW.currentItem().text())
        except:
            sh = self.shot
        try:
            vr = self.compOut_LW.currentItem().text()
        except:
            vr = self.compOut
        jpgOut= '%s/%s/film/%s/%s/%s/comp/compOut/%s/' % (self.dsComp, pr, ep, sq, sh, vr)
        #changed CompOut to compOut /daniel
        jpgList = os.listdir(jpgOut)
        if jpgList != []:
            for jpeg in jpgList:
                if jpeg.endswith(".jpg"):
                    image = jpgOut + jpeg
                    sg = sgTools.getSG()
                    shotObj =sgTools.sgGetShot(sg,sh,sq,pr,ep,['id'])
                    type = "Shot"
                    sgTools.sgThumbUpdate(type,shotObj,image)
            print "upated thumbnail for seleted shot"

    def updateRVPlugs(self):
        localPlug =os.listdir(self.rvRoot + '/plugins/Mu')
        netPlug = os.listdir(self.rvplugs)
        for plug in netPlug:
            try:
                shutil.copy(self.rvplugs + '/' + plug,self.rvRoot + '/plugins/Mu')
            except:
                pass
            
    def GetUser(self):
        ##Test and return if Episode exists
        self.User_CB.clear()
        self.userDict = {}
        self.userProject = {}
        self.group = {'type': 'Group', 'id': 5}
        self.myPeople = sgTools.sgGetPeople()
        for user in sorted(self.myPeople):
            if str(user['sg_status_list']) == "act":
                userName = str(user['name'])
                self.User_CB.addItem(userName)
                self.userDict[userName] = user['id']

    def versionUp(self):
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        sh = self.shots_LW.currentItem().text()
        ns = self.nukeScripts_LW.currentItem().text()
        nkScript = '%s/%s/film/%s/%s/%s/comp/nukeScripts/%s' % (self.dsComp, pr, ep, sq, sh,ns)

        verObj = re.search("[Vv][0-9][0-9][0-9]",nkScript)
        ver = verObj.group()
        sVer = verObj.start()
        eVer = verObj.end()
        oldVer = int(ver[-3:])
        nVer = 'v' + '%03d' % int(oldVer + 1)
        nNukeScript = nkScript[:sVer] + nVer + nkScript[eVer:]

        lns = self.nukeScripts_LW.item(0).text()
        topObj = re.search("[Vv][0-9][0-9][0-9]",lns)
        top = topObj.group()
        oldtop = int(top[-3:])
        newTop = 'v' + '%03d' % int(oldtop + 1)
        nNukeScript = nkScript[:sVer] + newTop + nkScript[eVer:]
        if not os.path.isfile(nNukeScript):
            shutil.copy(nkScript,nNukeScript)
            self.init_nukeScripts()

    def publishAction(self,us,pr,ep,sq,sh,co):
        '''
        Guts .. the good stuff!!
        '''
        
        dict = {}
        path = []
        src = r'%s/%s/film/%s/%s/%s/comp/compOut/%s' % (self.dsComp,pr, ep, sq, sh, co)
        srcRoot = src
        dstRoot = r'%s/%s/film/%s/%s/%s/published2D/compOut/' % (self.dsComp,pr, ep, sq, sh)
        dstDPX = r'%s/DPX' %(dstRoot)
        dstJPG = r'%s%s' %(dstRoot,'JPG')
        localQT = srcRoot
        dstQT = r'%s%s' %(dstRoot,'QT')
        dstPY = r'%s%s' %(dstRoot,'.py')
        if not os.path.exists(dstRoot): os.makedirs(dstRoot)
        if not os.path.exists(dstDPX): os.makedirs(dstDPX)
        if not os.path.exists(dstJPG): os.makedirs(dstJPG)
        if not os.path.exists(dstQT): os.makedirs(dstQT)
        if not os.path.exists(dstPY):os.mkdir(dstPY)
        outPutList = os.listdir(src)
        nkList = filter(lambda x:".nk" in x,outPutList)
        if nkList != []:
            rndFile = r'%s/%s' %(src, nkList[0])
            
            if os.path.exists(src):
                name, frames, extension = self.getFrameTime(src)
                start = min(frames)
                end = max(frames)
                frameOne = name + str(int(start)) + "-" + str(int(end)) + "#." + extension
                frameJpg = name + "####.jpg"
                frameMov = name + "mov"
                print '\tname:%s\n\tsrc:%s\n\tdst:%s\n\tstart:%s\n\tend:%s\n\textension:%s\n\tRender File:%s\n' % (name, src, dstRoot, start, end, extension,rndFile)
                src = src + "/" + frameOne
                self.testJpgFolder(srcRoot,dstJPG)
                filePath = srcRoot + "/" + name + str(start) + "." + extension
                sgTools.sgConvertIcon(filePath)
    
                pyList = os.listdir(dstPY)
                for py in pyList:
                    os.remove(dstPY + "/" + py)
                x,y = self.getImageInfo()
    
                if sys.platform == "linux2":
                    print "linux dork"
                else:
                    if self.actionDPX.isChecked():
                        srcSplit = src.split("/")
                        srcRoot = src.replace("/" + srcSplit[-1],"")
                        dstSplit = dstDPX.split("/")
                        dstRoot = dstDPX.replace("/" + dstSplit[-1],"DPX/")

                        print "working on " + dstRoot
                        print "//vfx-render-server/royalrender/bin/win/rrCopy.exe -sync " + srcRoot + " " +  dstRoot
                        os.system("//vfx-render-server/royalrender/bin/win/rrCopy.exe -sync " + srcRoot + " " +  dstRoot)
                        
                    if self.actionJPG.isChecked():
                        cmd = self.dsRvio("JPG",src,dstJPG + "/" + frameJpg,sq,pr,sh,x,y)
                        self.clearOut(str(dstJPG + "/"))
                        path = dstPY+ "/JPG.py"
                        bFile = open(path, 'w')
                        bFile.write("import subprocess\nproc = subprocess.call( '"+ cmd +"\')\nraw_input(\"Press Enter to continue...\")")
                        bFile.close()
                        dsSP.sp(path)
                        
                    if self.actionQT.isChecked():
                        cmd = self.dsRvio("QT",src, dstQT + "/" + frameMov,sq,pr,sh,x,y)
                        path = dstPY+ "/QT.py"
                        bFile = open(path, 'w')
                        bFile.write("import subprocess\nproc = subprocess.call( '"+ cmd +"')\nshutil.copy('"+ dstQT + "/" + frameMov + "','" + localQT + "/" + frameMov +"\')\nraw_input(\"Press Enter to continue...\")")
                        bFile.close()
                        dsSP.sp(path)
                        
            renderFile = rndFile
            pubPath = '%s/%s/film/%s/%s/%s/comp/compOut/' % ( self.dsComp,pr, ep, sq, sh)
            
            
            print pubPath
            #sgTools.sgPublish2DFrames(str(filePath),str(renderFile),str(us),pubPath)
            dsSP.spSG('sgTools.sgPublish2DFrames(\''+str(filePath)+'\',\''+str(renderFile)+'\',\''+ str(us)+'\',\''+ pubPath+'\')' )
            
            self.updateThumbs()
            self.save_config()

    def publish(self):

        us = self.User_CB.currentText()
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        sh = self.shots_LW.currentItem().text()
        co = self.compOut_LW.currentItem().text()
        self.publishAction(us,pr,ep,sq,sh,co)
        
    def publishSeq(self):
        print "Publishing Sequence"
        us = self.User_CB.currentText()
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        #sq = self.sequences_LW.currentItem().text()
        sqList = self.sequences_LW.selectedItems()
        
        for sequence in sqList:
            sq = sequence.text()
            seq = r'%s/%s/film/%s/%s' % (self.dsComp,pr, ep, sq)
            dsFilmCheck.dsPublishSequence(pr,ep,sq,seq)
            
    def testJpgFolder(self,srcRoot,dstJPG):
        tmpList = os.listdir(srcRoot)
        for tmp in tmpList:
            if tmp == "jpg":
                shutil.copy(srcRoot + "/",dstJPG)

    def copyFrames(self,src,dstDPX):   
        srcSplit = src.split("/")
        srcRoot = src.replace("/" + srcSplit[-1],"")
        dstSplit = dstDPX.split("/")
        dstRoot = dstDPX.replace("/" + dstSplit[-1],"DPX/")
           
        print "working on " + dstRoot
        shutil.rmtree(str(dstRoot))
               
        dsSP.spCOPY('print "Publishing '+ srcRoot + ' to ' + dstRoot + '"\nshutil.copytree(\''+str(srcRoot)+'\',\''+str(dstRoot)+'\')' )
        #shutil.copytree(srcRoot,dstRoot)

                        
    def getImageInfo(self):
        from time import sleep
        sleep(.5)
        pr = str(self.projects_CB.currentText())
        ep = str(self.episodes_CB.currentText())
        sq = str(self.sequences_LW.currentItem().text())
        try:
            sh = str(self.shots_LW.currentItem().text())
        except:
            sh = self.shot
            
        try:
            co = self.compOut_LW.currentItem().text()
        except:
            co = self.compOut
        
        compOut= '%s/%s/film/%s/%s/%s/comp/compOut/%s/' % (self.dsComp, pr, ep, sq, sh,co)
        frameList = os.listdir(compOut)
        if frameList != []:
            frameList.sort()
            for frame in frameList:
                if frame[-3:] == "jpg":
                    nFrame = frame
                    break
            image = compOut + nFrame
            img = Image.open(image)
            return img.size

    def clearOut(self,path):
        tmpFiles = os.listdir(path)
        for tmp in tmpFiles:
            os.remove(path + "/" + tmp)

    def dsRvio(self,type,src,dst,sq,pr,sh,x,y):
        if type == "JPG":
            if self.actionOverlays.isChecked():
                cmd = self.rvio + ' -vv [ %s -uncrop %s %s 0 50 ] -overlay frameburn 1 1 40 -overlay textburn "" "" "" "%s_%s" "duckling A/S = %s" "" 1 40.0 -outsrgb -o %s' % (src,x,y,sq,sh,pr,dst)
                return cmd
            else:
                cmd = self.rvio + ' -vv %s -outsrgb -o %s ' % (src, dst)
                return cmd

        if type == "QT":
            if self.actionOverlays.isChecked():
                percent = self.percent_CB.currentText()
                if percent == "100%":
                    cmd = self.rvio + ' -vv [ %s -uncrop %s %s 0 50 ] -overlay frameburn 1 1 40 -overlay textburn "" "" "" "%s_%s" "Duckling %s" "" 1 40.0 -codec avc1 -quality 0.75 -o %s' % (src,x,y,sq,sh,pr,dst)
                    return cmd
                if percent == "75%":
                    cmd = self.rvio + ' -vv [ %s -uncrop %s %s 0 50 ] -scale 0.75 -fps 25 -overlay frameburn 1 1 25 -overlay textburn "" "" "" "%s_%s" "duckling A/S = %s" "" 1 25.0 -codec avc1 -quality 0.75 -o %s' % (src,x,y,sq,sh,pr,dst)
                    return cmd
                if percent == "50%":
                    cmd = self.rvio + ' -vv [ %s -uncrop %s %s 0 60 ] -scale 0.5  -fps 25 -overlay frameburn 1 1 20 -overlay textburn "" "" "" "%s_%s" "duckling A/S = %s" "" 1 20.0 -outsrgb -o %s' % (src,x,y,sq,sh,pr,dst)
                    return cmd
                if percent == "25%":
                    cmd = self.rvio + ' -vv [ %s -uncrop %s %s 0 100 ] -scale 0.25 -fps 25 -overlay frameburn 1 1 10 -overlay textburn "" "" "" "%s_%s" "duckling A/S = %s" "" 1 10.0 -outsrgb -o %s' % (src,x,y,sq,sh,pr,dst)
                    return cmd
            else:
                cmd = self.rvio + ' -vv %s -outsrgb -o %s' % (src, dst)
                return cmd

    def checkVersion(self, path):
        '''
        Checks the path if there is any directories matching the pattern [vV]\d\d\d
        then adds it to a list and then it check which is the lastest and return it +1
        '''
        if os.path.exists(path):
            bool = True
            list = []
            for dir in os.listdir(path):
                match = re.search('([vV]\d\d\d)', dir)
                if match:
                    list.append(match.groups()[0].strip('v'))
            if list:
                list.sort()
                return 'v%03d' % (int(max(list)) + 1)
            else:
                return 'v001'
        else:
            return 'v001'

    def getFrameTime(self, path):
        '''
        Returns the name, amount of frames contained in a list and extensions
        From a path.
        '''
        list = []
        name = ''
        frameList = os.listdir(path)
        for frame in os.listdir(path):
            if frame.endswith('.exr') or frame.endswith('.dpx'):
                match = re.search('(.*)(\d\d\d\d)\.(\w*)', frame)
                if match:
                    name = match.groups()[0]
                    list.append(match.groups()[1])
                    extension = match.groups()[2]
        list.sort()
        if not self.checkMissingFrames(list):
            print 'Missing frames in', path
        return name, list, extension

    def checkMissingFrames(self,list):
        '''
        Check for missing frames, lets the users know if a stack is missing a file.
        '''
        number = '%04d' % int(list[0])
        for i in range(len(list)):
            if number == list[i]:
                number = '%04d' % (int(number) + 1)
            else:
                print 'Frame:', number,'!=',list[i]
                return False
        return True
    
    def check(self):
        '''
        Check if you have any selected compOut_LW push button is enabled else its greyed out.
        '''
        if self.compOut_LW.selectedItems():
           self.publish_B.setEnabled(True)
        else:
            self.publish_B.setEnabled(False)

    def refresh(self):
        '''
        Clears all the ComboBoxes and initializes to update.
        In order of project, episode, sequences
        Might change this since there is no reason to do anything
        else then clear everything and then init the project and let
        self.projects.currentIndexChanged.connect(self.init_episodes)
        do the rest...
        '''
        self.projects_CB.clear()
        self.init_projects()
        self.episodes_CB.clear()
        self.init_episodes()
        self.sequences_LW.clear()
        self.init_sequences()

    def init_projects(self):
        '''
        Adds projects to self.projects
        Only if the project contains a /Local/config.xml
        '''
        list = []
        project_path = self.dsPipe
        for dir in os.listdir(project_path):
            path = '%s/%s/.local/config.xml' % (project_path, dir)
            if os.path.exists(path):
                list.append(dir)

        list.sort()

        for project in list:
            self.projects_CB.addItem(project)

    def init_episodes(self):
        '''
        Adds episodes to self.episodes
        '''
        self.episodes_CB.clear()
        self.add(self.episodes_CB, '%s/%s/film' % (self.dsPipe, self.projects_CB.currentText()))

    def init_sequences(self):
        '''
        Adds sequences to self.sequences
        Searches after pattern is [qQ][0-9][0-9][0-9][0-9]
        '''
        self.sequences_LW.clear()
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        self.add(self.sequences_LW,  '%s/%s/film/%s' % (self.dsPipe, pr, ep), r'([qQ][0-9][0-9][0-9][0-9])')

    def init_shots(self):
        '''
        Adds shots to self.shots
        Searches after pattern is [sS][0-9][0-9][0-9][0-9]
        '''
        self.shots_LW.clear()
        self.compOut_LW.clear()

        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        self.add(self.shots_LW,  '%s/%s/film/%s/%s' % (self.dsPipe, pr, ep, sq), r'([sS][0-9][0-9][0-9][0-9])')

    def init_nukeScripts(self):
        '''
        Adds compOut to self.compOut.
        Searches after pattern is [Rr][Ll]
        '''
        list = []
        self.nukeScripts_LW.clear()
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()


        for item in self.shots_LW.selectedItems():
            sh = item.text()
            path= '%s/%s/film/%s/%s/%s/comp/nukeScripts' % (self.dsComp, pr, ep, sq, sh)
            if os.path.exists(path):
                for file in os.listdir(path):
                    if os.path.isfile('%s/%s' % (path, file)):
                        if file[-3:] == ".nk":
                            if not file in list:
                                txt = file
                                list.append(txt)
                                
        list.sort(reverse=True)
        for item in list:
                self.nukeScripts_LW.addItem(item)

    def init_compOut(self):
        '''
        Adds compOut to self.compOut.
        Searches after pattern is [Rr][Ll]
        '''
        list = []
        self.compOut_LW.clear()
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()

        for item in self.shots_LW.selectedItems():
            sh = item.text()
            path= '%s/%s/film/%s/%s/%s/comp/compOut' % (self.dsComp, pr, ep, sq, sh)
            if os.path.exists(path):
                for dir in os.listdir(path):
                    if os.path.isdir('%s/%s' % (path, dir)):
                        match = re.search('v[0-9][0-9][0-9]', dir)
                        if match and not dir in list:
                            version = str(dir)
                            list.append(version)
        list.sort(reverse=True)
        for item in list:
                self.compOut_LW.addItem(item)

    def add(self, QComboBox, path, pattern = ''):
        '''
        This adds directories that match with the pattern if any is passed along.
        '''
        list = []
        if os.path.exists(path):
            for dir in os.listdir(path):
                if os.path.isdir('%s/%s' % (path, dir)):
                    match = re.search(pattern, dir)
                    if match:
                        list.append(dir)
            list.sort()
            for item in list:
                QComboBox.addItem(item)

    def open_sequences(self):
        '''
        Opens sequences with a filebrowser(self.open)
        by double clicking a QListWidgetItem
        '''
        project = self.projects_CB.currentText()
        episode = self.episodes_CB.currentText()
        sequence = self.sequences_LW.currentItem().text()
        path = '%s/%s/film/%s/%s' % (self.dsPipe, project, episode, sequence)

        self.open(path)

    def open_shots(self):
        '''
        Opens shots with a filebrowser(self.open)
        by double clicking a QListWidgetItem
        '''
        project = self.projects_CB.currentText()
        episode = self.episodes_CB.currentText()
        sequence = self.sequences_LW.currentItem().text()
        shot = self.shots_LW.currentItem().text()
        path = '%s/%s/film/%s/%s/%s' % (self.dsPipe, project, episode, sequence, shot)

        self.open(path)

    def open_nukeScript(self):
        '''
        Opens shots with a filebrowser(self.open)
        by double clicking a QListWidgetItem
        '''
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        sh = self.shots_LW.currentItem().text()
        ns = self.nukeScripts_LW.currentItem().text()

        if sys.platform == "linux2":
            os.environ['NUKE_PATH'] = '/dsGlobal/globalNuke'
            os.environ['NUKE_PLUGINS_PATH'] = '/dsGlobal/globalNuke/plugins'
            os.environ['NUKE_GIZMO_PATH'] = '/dsGlobal/globalNuke/gizmos'
            os.environ['NUKE_PYTHON_PATH'] = '/dsGlobal/globalNuke/Python'
            os.environ['OFX_PLUGIN_PATH'] = '/dsGlobal/globalNuke/plugins/OFX/Linux/OFX'

            pathDir= '/dsComp/%s/film/%s/%s/%s/comp/nukeScripts/' % (pr, ep, sq, sh)
            pathNS='/dsComp/%s/film/%s/%s/%s/comp/nukeScripts/%s' % (pr, ep, sq, sh,ns)
            cmd = '/usr/local/Nuke6.3v7/Nuke6.3' + ' ' +  str(pathNS)
            self.process(cmd)
            #subprocess.Popen(cmd, creationflags = subprocess.CREATE_NEW_CONSOLE)

        else:
            os.environ['NUKE_PATH'] = '//vfx-data-server/dsGlobal/globalNuke'
            os.environ['NUKE_PLUGINS_PATH'] = '//vfx-data-server/dsGlobal/globalNuke/plugins'
            os.environ['NUKE_GIZMO_PATH'] = '//vfx-data-server/dsGlobal/globalNuke/gizmos'
            os.environ['NUKE_PYTHON_PATH'] = '//vfx-data-server/dsGlobal/globalNuke/python'
            os.environ['OFX_PLUGIN_PATH'] = '//vfx-data-server/dsGlobal/globalNuke/plugins/OFX/win64'
            sys.path.append("//vfx-data-server/dsGlobal/dsCore/nuke/PySide")

            pathDir= '%s/%s/film/%s/%s/%s/comp/nukeScripts/' % (self.dsComp, pr, ep, sq, sh)
            pathNS='%s/%s/film/%s/%s/%s/comp/nukeScripts/%s' % (self.dsComp, pr, ep, sq, sh,ns)
            cmd = 'C:/Program Files/Nuke6.3v7/Nuke6.3.exe' + ' ' +  str(pathNS)
            subprocess.Popen(cmd, creationflags = subprocess.CREATE_NEW_CONSOLE)

    def open_compOut(self):
        '''
        Opens compOut with self.viewer else with a filebrowser
        '''
        pr = self.projects_CB.currentText()
        ep = self.episodes_CB.currentText()
        sq = self.sequences_LW.currentItem().text()
        sh = self.shots_LW.currentItem().text()
        co = self.compOut_LW.currentItem().text()
        path= '%s/%s/film/%s/%s/%s/comp/compOut/%s' % (self.dsComp, pr, ep, sq, sh,co)

        name, frames, extension = self.getFrameTime(path)

        if str(self.default_viewer) == 'None':
            self.open(path)
        else:
            if self.viewer('%s/%s_####.%s' % (path, name.rstrip('_'), extension)):
                pass
            elif self.viewer( '%s/%s_@@@@.%s' % (path, name.rstrip('_'), extension)):
                pass
            else:
                self.viewer(path)

    def viewer(self, path):
        '''
        Opens path in the default viewer determined in the config file.
        If no default viewer specified in the config file then its opens the explore.
        '''

        if sys.platform == "linux2":
            cmd = "%s %s" % (self.default_viewer, path)

        if sys.platform == "win32":
            cmd = '%s %s' % (self.default_viewer, path.replace("/","\\"))
        try:
            #print cmd
            self.process(cmd)
            return True
        except Exception as e:
            #print e
            return False

    def open(self, path):
        '''
        Open explorer for windows
        or gnome-open on linux
        '''
        if sys.platform == "linux2":
            if os.path.exists(path):
                cmd = "gnome-open " + str(path)
            else:
                print path, 'doesnt exists.'
        if sys.platform == "win32":
            if os.path.exists(path):
                cmd = "explorer %s" % path.replace("/","\\")
            else:
                print path, 'doesnt exists.'
        try:
            self.process(cmd)
        except:
            pass

    def load_config(self):
        '''
        Load config which is a dictionary and applying setting.
        '''
        if os.path.exists(self.config_path):
            print 'Loading config file from:', self.config_path
            config_file = open( '%s' % self.config_path, 'r')
            list = config_file.readlines()
            config_file.close()

            config = {}
            for option in list:
                key, value = option.split('=')
                config[key] = value.strip()

            self.LUT_CB.setCurrentIndex(int(config.get('Lut')))


            index = [i for i in range(self.User_CB.count()) if self.User_CB.itemText(i) == config.get('USER')][0]
            self.User_CB.setCurrentIndex(index)

            index = [i for i in range(self.projects_CB.count()) if self.projects_CB.itemText(i) == config.get('PROJECT')][0]
            self.projects_CB.setCurrentIndex(index)

            index = [i for i in range(self.episodes_CB.count()) if self.episodes_CB.itemText(i) == config.get('EPISODE')][0]
            self.episodes_CB.setCurrentIndex(index)

            self.actionDPX.setChecked(int(config.get('actionDPX')))
            self.actionJPG.setChecked(int(config.get('actionJPG')))
            self.actionQT.setChecked(int(config.get('actionQT')))
            try:
                self.actionOverlays.setChecked(int(config.get('actionOverlays')))
            except:
                pass
            try:
                self.percent_CB.setCurrentIndex(int(config.get('percent')))
            except:
                pass
            index = [i for i in range(self.sequences_LW.count()) if self.sequences_LW.item(i).text() == config.get('SEQUENCE')][0]
            self.sequences_LW.setCurrentRow(index)

            items = [self.shots_LW.item(i) for i in range(self.shots_LW.count()) if str(self.shots_LW.item(i).text()) in config.get('SHOT')]
            for item in items:
                self.shots_LW.setCurrentRow(self.shots_LW.row(item))
                self.shots_LW.setItemSelected(item, 1)

            items = [self.compOut_LW.item(i) for i in range(self.compOut_LW.count()) if str(self.compOut_LW.item(i).text()) in config.get('RENDERLAYER')]
            for item in items:
                self.compOut_LW.setCurrentRow(self.compOut_LW.row(item))
                self.compOut_LW.setItemSelected(item, 1)

            try:
                self.default_viewer = str(config.get('default_viewer'))
            except:
                print 'default_viewer'

    def save_config(self):
        '''
        Save setting to the config file as a dictionary.
        '''
        user = self.User_CB.currentText()
        project = self.projects_CB.currentText()
        episode = self.episodes_CB.currentText()
        sequence = self.sequences_LW.currentItem().text()
        Lut = self.LUT_CB.currentIndex()
        percent = self.percent_CB.currentIndex()
        shot = [str(item.text()) for item in self.shots_LW.selectedItems()]
        rl = [str(item.text()) for item in self.compOut_LW.selectedItems()]
        if self.actionDPX.isChecked():
            actionDPX = 1
        else:
            actionDPX = 0
        if self.actionJPG.isChecked():
            actionJPG = 1
        else:
            actionJPG = 0
        if self.actionQT.isChecked():
            actionQT = 1
        else:
            actionQT = 0
        if self.actionOverlays.isChecked():
            actionOverlays = 1
        else:
            actionOverlays = 0
        if not os.path.exists(self.config_dir):
            #print self.config_dir, self.config_path
            os.mkdir(self.config_dir)
        config = open( '%s' % self.config_path, 'w')
        config.write('USER=%s\n' % (user))
        config.write('PROJECT=%s\n' % (project))
        config.write('EPISODE=%s\n' % (episode))
        config.write('SEQUENCE=%s\n' % (sequence))
        config.write('SHOT=%s\n' % (shot))
        config.write('RENDERLAYER=%s\n' % (rl))
        config.write('actionDPX=%s\n' % (actionDPX))
        config.write('actionJPG=%s\n' % (actionJPG))
        config.write('actionQT=%s\n' % (actionQT))
        config.write('actionOverlays=%s\n' % (actionOverlays))
        config.write('Lut=%s\n' % (str(Lut)))
        config.write('percent=%s\n' % (str(percent)))
        if self.default_viewer: config.write('default_viewer=%s\n' % (self.default_viewer))
        config.close()

        self.load_config()
        return self.config_path

    def process( self, cmd_line):
        '''
        Subprocessing, Returning the process.
        '''
        cmd = cmd_line.split(' ')
        proc = subprocess.Popen(cmd,
                            shell=False,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            )
        return proc

def publishFromRV():
    '''For running publishStandalone class'''
    app = QtGui.QApplication(['//vfx-data-server/dsGlobal/dsCore/tools/dsProjectCreate/dsPublish2D.py'])
    instance = publishStandalone()
    instance.show()
    sys.exit(app.exec_())


def publish():
    '''For running publishStandalone class'''
    app = QtGui.QApplication(sys.argv)
    instance = publishStandalone()
    instance.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    publish()
