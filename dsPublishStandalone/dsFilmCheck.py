import os, glob, time, re, shutil
from time import gmtime, strftime

def writeLog(path,info):
    logFile = open(path, 'a')
    dateStamp = strftime("%S-%M-%H", gmtime())
    logFile.write(dateStamp + " : " + info)
    logFile.close()

def getLatestVer(path):
    verList = []
    tmpList = os.listdir(path)
    for f in tmpList:
        if re.search("v[0-9][0-9][0-9]",f):
            verList.append(f)
    verList.sort()
    return verList[-1]

def compare(pathA,pathB,logPath):
    for comp in glob.glob(pathB):
        for file in os.listdir(comp):
            filePath = '%s/%s' % (comp, file)
            filePath = filePath.replace('\\', '/')
            if file.endswith('.dpx'):
                if not os.path.exists(pathA):
                    #os.makedirs(pathA)
                    info = "create dir for " + pathA + "\n"
                    writeLog(logPath,info)
                    
                online_file = '%s/%s' % (pathA, file)
                
                if not os.path.isfile(online_file):
                    info = "online: " + filePath + " copyied to " + online_file + "\n"
                    writeLog(logPath,info)
                    print info
                    shutil.copy2(filePath, online_file)
                    
                else: 
                    online_ctime = os.stat(online_file)[8]
                    online_size = os.stat(online_file)[6]
                    file_ctime = os.stat(filePath)[8]
                    file_size = os.stat(filePath)[6]
                    if file_ctime > online_ctime or file_size > online_size:
                        info = "online: %s %s" %(file, time.ctime(online_ctime)), "compout: %s %s" %(file, time.ctime(file_ctime))
                        info = str(info) + "\n"
                        writeLog(logPath,info)
                        print info
                        #shutil.copy2(filePath, online_file)
            
def runSequence(path,logPath):
    if os.path.isdir(path):
        tmpList = os.listdir(path)
        for f in tmpList:
            if re.search("s[0-9][0-9][0-9]",f):
                info = path + "/" + f + "\n"
                writeLog(logPath,info)
                pathA = path + "/" + f + "/published2D/compOut/DPX"
                tmpPath = path + "/" + f + "/comp/compOut"
                t = os.listdir(tmpPath)
                if len(t) < 0:
                    if os.path.isdir(tmpPath):
                        ver = getLatestVer(path + "/" + f + "/comp/compOut")
                        pathB = path + "/" + f + "/comp/compOut/" + ver
                        compare(pathA,pathB,logPath)
                    else:
                        info = "ERROR: " + tmpPath + " dosen't exist" + "\n"
                        writeLog(logPath,info)
                else:
                    info = "No Versions in:" + tmpPath + "\n"
                    writeLog(logPath,info)
    
    else:
        info = "ERROR: " + path + " dosen't exist" + "\n"
        writeLog(logPath,info)

def createLogPath():
    baseLog = "//vfx-data-server/dsGlobal/dsCore/tools/dsPublishStandalone/logs/"
    if not os.path.isdir(baseLog):os.makedirs(baseLog)
    
    fileName = strftime("%d-%m-%y", gmtime())
    logPath = baseLog + fileName + ".txt"
    return logPath

def dsPublishSequence(proj,epi,seq,pathToSeq):
    logPath = createLogPath(pathToSeq)
    
    tmpPath = "//xserv2.duckling.dk/dsComp/" + proj + "/film/" + epi + "/" + seq
    info = tmpPath + "\n"
    print info
    
    writeLog(logPath,info)
    runSequence(tmpPath,logPath)

def runEpisode(path,logPath):
    tmpList = os.listdir(path)
    for seq in tmpList:
        if re.search("q[0-9][0-9][0-9]",seq):
            tmppath = path + "/" + seq
            info = tmppath + "\n"
            writeLog(logPath,info)
            runSequence(tmppath,logPath)


def OnlineUpdate():
    logPath = createLogPath()

    episode = "littleHelpers_013693"
    #episode = "LEGO_Friends_Intro_011856"
    path = "//xserv2.duckling.dk/dsComp/HK/film/" + episode
    runEpisode(path,logPath)
    
OnlineUpdate()
