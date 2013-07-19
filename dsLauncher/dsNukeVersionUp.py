
import re,os,sys,subprocess,shutil

class dsNukeVersionUp:
    def __init__(self,arg1,arg2):
        ''' usage.. add full path to nukeScript. Autogenerates nukeScipt version up in same folder. Needs compOut compIn and nukeScipts folders... '''
        self.nPath = arg1
        self.val = arg2
        pathSplit = self.nPath.split("/")
        self.nScript = pathSplit[-1]
        nScriptInfo = self.nScript.split("_")
        ## split up nukseScript name too vars from the back...
        if len(pathSplit) < 10:
            self.vendor = nScriptInfo[-9]
            self.product = nScriptInfo[-8]
            self.episode = nScriptInfo[-7]
            self.seq = nScriptInfo[-6]
            self.shot = nScriptInfo[-5]
            self.version = nScriptInfo[-4]
            self.type = nScriptInfo[-3]
            self.nn = nScriptInfo[-2]
            self.user = nScriptInfo[-1][:-3]
            self.nsLocation = self.nPath.replace(self.nScript,"")
            self.newNukeScript = self.nScriptNewName()
        else:
            self.episode = nScriptInfo[-7]
            self.seq = nScriptInfo[-6]
            self.shot = nScriptInfo[-5]
            self.version = nScriptInfo[-4]
            self.type = nScriptInfo[-3]
            self.nn = nScriptInfo[-2]
            self.user = nScriptInfo[-1][:-3]
            self.nsLocation = self.nPath.replace(self.nScript,"")
            self.newNukeScript = self.nScriptNewName()
        
        if self.val == "reSub":
            self.updateReads()
        if self.val == "find":
            self.checkReads()
        if self.val == "history":
            self.historyRL()
        if self.val == "backUp":
            self.backupNS()
            
            
    def backupNS(self):
        ''' loads nuke scipt, Finds latest read and cross checks version with published3d.. creates History with verion number '''
        
        print "backingUp Renderlayers and NS"
        template_handle = open(self.nPath, 'r')
        for line in template_handle:
            newLine = line
            if re.search("compIn",line):
                cVersion = self.reVersion(line)
                rlPath = newLine.strip(" file \n")
                rlList = rlPath.split("/")
                rlPath = rlPath.replace('/' + str(rlList[-1]),"")
                rlRootPath = rlPath.replace('/'+ str(rlList[-2]), "")
                
                cVar = re.search('v\d{3}',cVersion).group()
                if re.search("//vfx-data-server",rlRootPath):
                    backupPath = rlRootPath.replace("Film","Backup/Film")
                if re.search("P:/",rlRootPath):
                    backupPath = rlRootPath.replace("Film","Backup/Film")
                print rlRootPath
                print self.nPath
                if os.path.isfile(self.nPath):
                    nukeBackupPath = self.nsLocation.replace("Film","Backup/Film")
                    if not os.path.isdir(nukeBackupPath):
                        os.makedirs(nukeBackupPath)
                        #print self.nsLocation
                        #print nukeBackupPath + self.nScript
                        shutil.copy(self.nPath,nukeBackupPath + self.nScript)
                if os.path.isdir(rlRootPath + "/" + cVar):
                    if not os.path.isdir(backupPath + "/" + cVar):
                        shutil.copytree(rlRootPath + "/" + cVar, backupPath + "/" + cVar)
        template_handle.close()

    def historyRL(self):
        ''' loads nuke scipt, Finds latest read and cross checks version with published3d.. creates History with verion number '''
        template_handle = open(self.nPath, 'r')
        for line in template_handle:
            newLine = line
            if re.search("compIn",line):
                cVersion = self.reVersion(line)
                rlPath = newLine.strip(" file \n")
                rlList = rlPath.split("/")
                rlPath = rlPath.replace('/' + str(rlList[-1]),"")
                rlRootPath = rlPath.replace('/'+ str(rlList[-2]), "")
                hisPath = rlRootPath + "/history"

                rlVList = self.getrlRootVersion(rlRootPath)
                for v in rlVList:
                    cVar = re.search('v\d{3}',cVersion).group()
                    vVar = re.search('v\d{3}',v).group()
                    if cVar < vVar:
                        if not os.path.isdir(hisPath):
                            os.mkdir(hisPath)
                            print "created history Folder"
                        print rlRootPath + "/" + vVar
                        shutil.move(rlRootPath + "/" + vVar,hisPath)
        template_handle.close()

    def checkReads(self):
        ''' loads Nuke script, checks if there a new version of a RL on the network returns bool '''
        x = 0
        ''' loads nuke scipt, Checks if there is a new RL available'''
        template_handle = open(self.nPath, 'r')
        for line in template_handle:
            if re.search("compIn",line):
                cVersion = self.reVersion(line)
                nVersion = self.rlTest(line)
                if cVersion != nVersion:
                    x = x + 1
            if x > 0:
                if re.search("compOut",line):
                    cVersion = self.reVersion(line)
                    nVersion = self.compOut(cVersion)
                    if cVersion != nVersion:
                        x = x + 1
        template_handle.close()
        if x != 0:
            return True
        else:
            return False

    def nScriptNewName(self):
        ''' takes self.version and versions up '''
        newVersion = self.versionUp(self.version)
        nScriptName = self.nScript.replace(self.version,newVersion)
        return nScriptName

    def reVersion(self,str):
        ''' takes path string and returns re.search of the v000 '''
        if re.search('v\d{3}',str):
            version = re.search("v\d{3}",str)
            currentVersion = version.group()
            return currentVersion
        else:
            currentVersion = None
            return currentVersion

    def versionUp(self,ver):
        ''' takes version string v000 and versions up '''
        numVal = int(ver[-3:])
        newVersion = 'v%03d' %int(numVal + 1)
        return newVersion 

    def compOut(self,ver):
        ''' takes version v000. finds compOut location and creates proper version folder if needed.'''
        if ver != None:
            nVer = self.versionUp(ver)
            self.compOutLoc = self.nsLocation.replace('nukeScripts','compOut')
            if os.path.isdir(self.compOutLoc):
                if not os.path.isdir(self.compOutLoc + nVer):
                    self.compOutFolder = self.compOutLoc + nVer
                    return nVer
                else:
                    self.compOutFolder = self.compOutLoc + nVer
                    return nVer
        else:
            return None
            
    def rlTest(self,path):
        ''' add path from nukscript strip down to fileNode compare to listDir to RL version's returns latest version from RL '''
        rlPath = path.strip(" file \n")
        rlList = rlPath.split("/")
        rlPath = rlPath.replace('/' + str(rlList[-1]),"")
        rlRootPath = rlPath.replace('/'+ str(rlList[-2]), "")
        if os.path.isdir(rlRootPath):
            rlVerList = self.getrlRootVersion(rlRootPath)
            return rlVerList[-1]
        
    def getrlRootVersion(self,rlRootPath):
        ''' add RL root path.. ie fullPaty/beauty_RL and returns list of versions in folder '''
        if os.path.isdir(rlRootPath):
            verList = os.listdir(rlRootPath)
            verList.sort()
            return verList
        else:
            verList = []
        return verList

    def updateReads(self):
        ''' loads nuke scipt, replaces version on Reads and writes then saves a versionUp '''
        x = 0
        template_handle = open(self.nPath, 'r')
        template_file = open(self.nsLocation + self.newNukeScript, 'w')
        for line in template_handle:
            newLine = line
            if re.search("compIn",line):
                cVersion = self.reVersion(line)
                nVersion = self.rlTest(line)
                if cVersion != nVersion:
                    x = x + 1
                    newLine = newLine.replace(cVersion,nVersion)
            if x > 0:
                if re.search("compOut",line):
                    cVersion = self.reVersion(line)
                    nVersion = self.compOut(cVersion)
                    if cVersion != nVersion:
                        x = x + 1
                        newLine = newLine.replace(cVersion,nVersion)
            template_file.write(newLine)
        template_handle.close()
        template_file.close()

        if x == 0:
            print self.nScript + " no New RenderLayers nothing to do"
            os.remove(self.nsLocation + self.newNukeScript)
        else:
            print "new renderlayers present autogenerated nukescript = " + self.nsLocation + self.newNukeScript
            print self.compOutFolder
            os.mkdir(self.compOutFolder)
            self.autoLoadRRFile(self.nsLocation + self.newNukeScript)
            shutil.copy(self.nsLocation + self.newNukeScript, self.compOutFolder + "/" + self.newNukeScript)
    
    def dsProcess( self, cmd_line):
        cmd = cmd_line.split(' ')
        proc = subprocess.Popen(cmd, 
                            shell=False,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            )
        return proc
    
    def autoLoadRRFile(self,rrFile):
        if sys.platform == "win32":
            command = '//vfx-render-manager/royalrender/bin/win/rrSubmitterconsole.exe ' + str(rrFile) +' UserName=0~' + str(self.user)  + ' DefaulClientGroup=1~' + 'All' + ' Priority=2~70 RRO_AutoApproveJob=3~False'
            print self.dsProcess(command).communicate()[0]
        print "submitted to Farm"

#nPath = '//vfx-data-server/dsPipe/munchRolls/Film/cryingGirl/q0010/s0150/comp/nukeScripts/munchRolls_nestle_cryingGirl_q0001_s0150_v003_comp_nn_ak.nk'
#ns = dsNukeVersionUp(nPath)