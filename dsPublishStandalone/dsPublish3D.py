print 'v1.0.6,',

import sys, os, glob, time, re, shutil, subprocess, hashlib, random
#from multiprocessing import mp

#### declare poper server ####
if sys.platform == 'linux2':
    sys.path.append('/dsGlobal/globalMaya/Python/PyQt_Linx64')
    sys.path.append('/dsGlobal/dsCore/shotgun')
    sys.path.append(r'/dsGlobal/dsCore/maya/dsCommon')
    from PyQt4 import QtGui, QtCore, uic
    form_class, base_class = uic.loadUiType("/dsGlobal/dsCore/tools/dsPublishStandalone/dsPublish3D.ui")

else:
    sys.path.append(r'\\vfx-data-server\dsGlobal\globalMaya\Python\PyQt_Win64')
    sys.path.append(r'\\vfx-data-server\dsGlobal\dsCore\shotgun')
    sys.path.append(r'\\vfx-data-server\dsGlobal\dsCore\maya\dsCommon')
    from PyQt4 import QtGui, QtCore, uic
    form_class, base_class = uic.loadUiType(r"\\vfx-data-server\dsGlobal\dsCore\tools\dsPublishStandalone\dsPublish3D.ui")

import sgTools
import dsFolderStruct as dsFS
import dsSubProcess as dsSP

class publishStandalone(form_class, base_class):
    '''
    Standalone tool for publishing frame stacks.
    Config file location user/config.ini
    '''
    def __init__(self, parent=None):
        base_class.__init__(self, parent)
        self.setupUi(self)
        self.push.setEnabled(False)
        self.default_viewer = None
        
        if sys.platform == "linux2":
            self.dsPipe = '/dsPipe'
            self.dsComp = '/mounts/dsComp'
            self.home = os.getenv("HOME")
            self.config_dir = '%s/.publish3D' % (self.home)
            self.config_path = '%s/config.ini' % (self.config_dir)
            
        elif sys.platform == 'win32':
            self.dsPipe = '//vfx-data-server/dsPipe'
            self.dsComp = '//xserv2.duckling.dk/dsComp'
            self.home = 'C:%s' % os.getenv("HOMEPATH")
            self.config_dir = '%s/.publish3D' % (self.home)
            self.config_dir = self.config_dir.replace("/","\\")
            self.config_path = '%s/config.ini' % (self.config_dir)
            self.config_path = self.config_path.replace("/","\\")
        
        self.shots.setSelectionMode(2)
        self.renderlayers.setSelectionMode(2)
        
        self.refresh()
        
        self.projects.currentIndexChanged.connect(self.init_episodes)
        self.episodes.currentIndexChanged.connect(self.init_sequences)
        
        self.sequences.itemSelectionChanged.connect(self.init_shots)
        self.sequences.itemDoubleClicked.connect(self.open_sequences)
        
        self.shots.itemSelectionChanged.connect(self.init_renderlayers)
        self.shots.itemDoubleClicked.connect(self.open_shots)
        
        self.renderlayers.itemDoubleClicked.connect(self.open_renderlayers)
        self.renderlayers.itemSelectionChanged.connect(self.check)

        self.push.clicked.connect(self.publish)
        self.refreshButton.clicked.connect(self.save_config)
        self.sgGetUser()
        self.load_config()

    def setServer(self):
        if sys.platform == 'linux2':
            return '/dsComp'
        else:
            return '//xserv2.duckling.dk/dsComp'
        '''
        if self.actiondsPipe.isChecked():
            if sys.platform == 'linux2':
                return '/dsPipe'
            else:
                return '//vfx-data-server/dsPipe'

        if self.actiondsComp.isChecked():
            if sys.platform == 'linux2':
                return '/dsComp'
            else:
                return '//xserv2.duckling.dk/dsComp'
        '''
    def sgGetUser(self):
        ##Test and return if Episode exists
        self.User_CB.clear()
        self.userDict = {}
        self.userProject = {}
        self.group = {'type': 'Group', 'id': 5}
        self.myPeople = sgTools.sgGetPeople()
        for user in self.myPeople:
            userName = str(user['name'])
            self.User_CB.addItem(userName)
            self.userDict[userName] = user['id']
    
    def publish(self):
        '''
        Publish your selection.
        scr :
            RawRender - render frames
        dst :
            
            comp/CompIn/PublishedCG - published frames
            comp/NukeScript - nukefile
        '''
        us = self.User_CB.currentText()
        pr = self.projects.currentText()
        ep = self.episodes.currentText()
        sq = self.sequences.currentItem().text()
        dict = {}
        path = []
        for shot in self.shots.selectedItems():
            sh = shot.text()
            for renderlayer in self.renderlayers.selectedItems():
                try:
                    rl = renderlayer.text()
                    destServer = self.setServer()
                    shotRoot = '%s/%s/film/%s/%s/' % (self.dsPipe,pr, ep, sq)
                    destRoot = '%s/%s/film/%s/%s/' % (self.dsComp,pr, ep, sq)
                    src = '%s/%s/film/%s/%s/%s/rawRender/%s' % (self.dsPipe,pr, ep, sq, sh, rl)
                    self.cleanRawRender(src)
                    dst = '%s/%s/film/%s/%s/%s/comp/published3D/%s' % (destServer, pr, ep, sq, sh, str(rl).replace('RL', '').rstrip('_'))
    
                    rndFile = '%s/%s/film/%s/%s/renderFiles' % (self.dsPipe,pr, ep, sq)
                    rFiles = os.listdir(rndFile)
                    maList = filter(lambda x:".ma" in x, rFiles)
                    xmlList = filter(lambda x:".xml" in x, rFiles)
                    xmlList.sort()
                    xmlFile = ""
                    
                    ### is present made bye submitter ###
                    for xml in xmlList:
                        if re.search(str(sh),xml):
                            if re.search(str(rl),xml):
                                xmlFile = xml
                                versionObj = re.search("v[0-9][0-9][0-9]",xml)
                                ver = versionObj.group()
                    ### if there is no Renderfile present ####
                    if xmlFile == "":
                        xmlFile = self.createTmpRfile(rndFile,sh,rl,"")
                        versionObj = re.search("v[0-9][0-9][0-9]",xmlFile)
                        ver = versionObj.group()
                    else:
                        #### check if xml has a ma file with it#####
                        ### if no ma file with the xml count and version up ####
                        rFfile = str(xmlFile[:-4]) + ".ma"
                        if not rFfile in maList:
                            print "creating new version of submitterless renderfile"
                            xmlSplit = xmlFile.split("_")
                            verSplit = xmlSplit[-1].split(".")
                            verTmp = verSplit[0]
                            ver = "v%03d"%(int(verTmp[-3:]) + 1)
                            xmlFile = self.createTmpRfile(rndFile,sh,rl,ver)
                        else:
                            print "match"

                    rndFile = '%s/%s' % (rndFile, xmlFile)
                    dst = '%s/%s' % (dst, ver)
                    
                    dsFS.dsCreateFs("COMP",destRoot ,sh)

                    if not os.path.exists(dst):
                        os.makedirs(dst)

                    if os.path.exists(src):
                        frameList = os.listdir(src)
                        if len(frameList) > 0:
                            name, frames, extension = self.getFrameTime(src)
                            start = min(frames)
                            end = max(frames)
                            fulsrc = '%s/%s_%s.%s' %(src,str(rl),start,extension)
                            print '\tname:%s\n\tsrc:%s\n\tdst:%s\n\tstart:%s\n\tend:%s\n\textension:%s\n\trawRender Path:%s\n\tRender File:%s\n' % (name, src, dst, start, end, extension,fulsrc,rndFile)

                            if self.checkBox.checkState():
                                tmpList = os.listdir(dst)
                                if len(tmpList) == 0:

                                    self.copyFrames(name, src, dst, start, end, extension)
                                else:
                                    print "frames present"
                            else:
                                self.rrSubmit(self.createNukePublish(name, src, dst, start, end, extension), start, end)
                            
                            serverSplit = destServer.split("/")
                            pubPath = '%s/%s/film/%s/%s/%s/comp/published3D/%s/%s' % (serverSplit[-1], pr, ep, sq, sh, str(rl).replace('RL', '').rstrip('_'),ver)
                            
                            #dsSP.spSG('sgTools.sgPublish3DFrames(\''+str(fulsrc)+'\',\''+str(renderFile)+'\',\''+ str(us)+'\',\''+ pubPath+'\')' )
                        else:
                            print "!!!!!!!!no frames in your RenderLayer.. PLease check your renders have been rendered!!!!!!!!"
                except:
                    pass

        self.save_config()

    def createTmpRfile(self,rndFile,sh,rl,ver):
        tmpList = os.listdir(rndFile)
        verList = []
        if ver == "":
            for file in tmpList:
                if re.search(".xml",file):
                    if re.search(str(rl),file):
                        verList.append(file)
            
            ver = "v%03d" %(len(verList)+1)
        
        print "creating empty maya file in renderFiles dir " + rndFile + sh + "_" + rl + "_" + ver + ".xml"
        
        if not os.path.isfile(rndFile + "/" + sh + "_" + rl + "_" + ver + ".xml"):
            f = open(rndFile + "/" + sh + "_" + rl + "_" + ver + ".xml", "wb")
            f.close()
        return sh + "_" + rl + "_" + ver + ".xml"

    def cleanRawRender(self,path):
        tmpList = os.listdir(path)
        tmpList.sort()
        for file in tmpList:
            if re.search("_broken_",file):
                os.remove(path + "/" + file)
                print path + "/" + file + " was removed"
                
            if re.search(".exrsl",file):
                os.remove(path + "/" + file)
                print path + "/" + file + " was removed"
                
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
        for frame in os.listdir(path):
            if frame.endswith('.exr'):
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
            
    def createNukePublish(self, name, src, dst, start, end, extension):
        '''
        Creates a nuke publish file which is submitted to royal render
        this isnt getting used in dsPublish commercial but i left it in.
        '''
        match = re.search('(\w*[rR][lL])', src)
        if match:
            renderlayer = match.groups()[0]
        
        filename = '%s_%03d_Publish_%s' % ( name.rstrip('.'), random.randint(0, 999),  renderlayer)
        if sys.platform == "linux2":
            nukefile = '/dsPantry/tmp/%s.nk' % (filename)
        else:
            nukefile = '//vfx-data-server/dsPantry/tmp/%s.nk' % (filename) 
        
        input = '%s/%s_####.%s' % (src, name.rstrip('.-'), extension)
        output = '%s/%s.####.%s' % (dst, name.rstrip('.-'), extension)
        
        file = open(nukefile,'w')
        file.write('Read {\n')
        file.write(' file %s\n' % input)
        file.write(' first %s\n' % start)
        file.write(' last %s\n' % end)
        file.write(' on_error black\n')
        file.write('}\n')
        
        file.write('Write {\n')
        file.write(' channels all \n')
        file.write(' file %s\n'% output)
        file.write(' file_type exr \n')
        file.write(' autocrop true \n')
        file.write(' on_error black \n')
        file.write('}\n')
        file.close()
        
        return nukefile

    def copyFrames(self, name, src, dst, start, end, extension):
        '''
        Copy frames from src to dst.
        '''
        match = re.search('(\w*[rR][lL])', src)
        if match:
            renderlayer = match.groups()[0]
        for number in range(int(start), int(end)+1):
            input = '%s/%s%04d.%s' % (src, name, number, extension)
            noDotName = name.replace('.', '').rstrip('_')
            output = '%s/%s.%04d.%s' % (dst, noDotName, number, extension)
            if os.path.exists(input):
                print 'copying:', input, output
                shutil.copy2( input, output)
            else:
                print 'Missing:', input
        
    def rrSubmit(self, nukeScript, startFrame, endFrame):
        '''
        Submit to royal render
        '''
        
        globals = '-Version 6.37 UserName=1~Publish Priority=2~80 DefaulClientGroup=1~RFarm CropEXR=1~0'
        if sys.platform == "linux2":
            cmd = "/mnt/rrender/bin/lx64/rrSubmitterconsole %s -SeqStart %s -SeqEnd %s %s" % (nukeScript, startFrame, endFrame, globals)
        elif sys.platform == "win32":
            cmd = "//vfx-render-server/royalrender/bin/win/rrSubmitterconsole.exe %s -SeqStart %s -SeqEnd %s %s" % (nukeScript, startFrame, endFrame, globals)

        print self.process(cmd).communicate()[0]
    
    def check(self):
        '''
        Check if you have any selected renderlayers push button is enabled else its greyed out.
        '''
        if self.renderlayers.selectedItems():
           self.push.setEnabled(True)
        else:
            self.push.setEnabled(False)
        
    def refresh(self):
        '''
        Clears all the ComboBoxes and initializes to update.
        In order of project, episode, sequences
        Might change this since there is no reason to do anything 
        else then clear everything and then init the project and let
        self.projects.currentIndexChanged.connect(self.init_episodes)
        do the rest...
        '''
        self.projects.clear()
        self.init_projects()
        self.episodes.clear()
        self.init_episodes()
        self.sequences.clear()
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
            self.projects.addItem(project)
              
    def init_episodes(self):
        '''
        Adds episodes to self.episodes 
        '''
        self.episodes.clear()
        self.add(self.episodes, '%s/%s/film' % (self.dsPipe, self.projects.currentText()))
            
    def init_sequences(self):
        '''
        Adds sequences to self.sequences 
        Searches after pattern is [qQ][0-9][0-9][0-9][0-9]
        '''
        self.sequences.clear()
        pr = self.projects.currentText()
        ep = self.episodes.currentText()
        self.add(self.sequences,  '%s/%s/film/%s' % (self.dsPipe, pr, ep), r'([qQ][0-9][0-9][0-9][0-9])')
    
    def init_shots(self):
        '''
        Adds shots to self.shots 
        Searches after pattern is [sS][0-9][0-9][0-9][0-9]
        '''
        self.shots.clear()
        self.renderlayers.clear()

        pr = self.projects.currentText()
        ep = self.episodes.currentText()
        sq = self.sequences.currentItem().text()
        self.add(self.shots,  '%s/%s/film/%s/%s' % (self.dsPipe, pr, ep, sq), r'([sS][0-9][0-9][0-9][0-9])')
    
    def init_renderlayers(self):
        '''
        Adds renderlayers to self.renderlayers.
        Searches after pattern is [Rr][Ll]
        '''
        list = []
        self.renderlayers.clear()
        pr = self.projects.currentText()
        ep = self.episodes.currentText()
        sq = self.sequences.currentItem().text()

        for item in self.shots.selectedItems():
            sh = item.text()
            #path= '%s/%s/film/%s/%s/%s/rawRender' % (self.dsPipe, pr, ep, sq, sh)
            path= '%s/%s/film/%s/%s/%s/rawRender' % (self.dsPipe, pr, ep, sq, sh)
            if os.path.exists(path):
                for dir in os.listdir(path):
                    if os.path.isdir('%s/%s' % (path, dir)):
                        match = re.search('[rR][lL]', dir)
                        if match and not dir in list:
                            list.append(dir)
        for item in list:
                self.renderlayers.addItem(item)

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
        project = self.projects.currentText()
        episode = self.episodes.currentText()
        sequence = self.sequences.currentItem().text()
        path = '%s/%s/film/%s/%s' % (self.dsPipe, project, episode, sequence)
            
        self.open(path)
    
    def open_shots(self):
        '''
        Opens shots with a filebrowser(self.open)
        by double clicking a QListWidgetItem
        '''
        project = self.projects.currentText()
        episode = self.episodes.currentText()
        sequence = self.sequences.currentItem().text()
        shot = self.shots.currentItem().text()
        path = '%s/%s/film/%s/%s/%s' % (self.dsPipe, project, episode, sequence, shot)
        
        self.open(path)

    def open_renderlayers(self):
        '''
        Opens renderlayers with self.viewer else with a filebrowser
        '''
        project = self.projects.currentText()
        episode = self.episodes.currentText()
        sequence = self.sequences.currentItem().text()
        shot = self.shots.currentItem().text()
        rl = self.renderlayers.currentItem().text()
        path = '%s/%s/film/%s/%s/%s/rawRender/%s' % (self.dsPipe, project, episode, sequence, shot, rl)
        
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
            print cmd
            self.process(cmd)
            return True
        except Exception as e:
            print e
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
            
            index = [i for i in range(self.User_CB.count()) if self.User_CB.itemText(i) == config.get('USER')][0]
            self.User_CB.setCurrentIndex(index)        
    
            index = [i for i in range(self.projects.count()) if self.projects.itemText(i) == config.get('PROJECT')][0]
            self.projects.setCurrentIndex(index)
            
            index = [i for i in range(self.episodes.count()) if self.episodes.itemText(i) == config.get('EPISODE')][0]
            self.episodes.setCurrentIndex(index)
            
            index = [i for i in range(self.sequences.count()) if self.sequences.item(i).text() == config.get('SEQUENCE')][0]
            self.sequences.setCurrentRow(index)
            
            items = [self.shots.item(i) for i in range(self.shots.count()) if str(self.shots.item(i).text()) in config.get('SHOT')]
            for item in items:
                self.shots.setCurrentRow(self.shots.row(item))
                self.shots.setItemSelected(item, 1)
                
            items = [self.renderlayers.item(i) for i in range(self.renderlayers.count()) if str(self.renderlayers.item(i).text()) in config.get('RENDERLAYER')]
            for item in items:
                self.renderlayers.setCurrentRow(self.renderlayers.row(item))
                self.renderlayers.setItemSelected(item, 1)
                
            try: 
                self.default_viewer = str(config.get('default_viewer'))
            except:
                print 'default_viewer'
            
    def save_config(self):
        '''
        Save setting to the config file as a dictionary.
        '''
        user = self.User_CB.currentText()
        project = self.projects.currentText()
        episode = self.episodes.currentText()
        sequence = self.sequences.currentItem().text()
        #shot = self.shots.currentItem().text()
        shot = [str(item.text()) for item in self.shots.selectedItems()] 
        rl = [str(item.text()) for item in self.renderlayers.selectedItems()]
        
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
        if self.default_viewer: config.write('default_viewer=%s\n' % (self.default_viewer))
        config.close()
        
        self.load_config()
        return self.config_path

    def process(self, cmd_line):
        '''
        Using subprocess.Popen to start a new process
        Returning the process when its started.
        '''
        cmd = cmd_line.split(' ')
        proc = subprocess.Popen(cmd, 
                            shell=False,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            )
        return proc

def publish():
    '''For running publishStandalone class'''
    app = QtGui.QApplication(sys.argv)
    instance = publishStandalone()
    instance.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    publish()
