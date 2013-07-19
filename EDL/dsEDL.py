'''
Created on 16/04/2013

@author: david
-parse through Premiere EDL 
    +work with any shot / sequence nameing convention... sc010.. 
    +return shots and sequences via clip names "q0010_s0010"
    -work with wipes
    -add / update shotgun thumbnails, start, end, compress and upload movie file..
    
    ***future***
    -create shotgun playlist
    -attach with ALE
    
'''
import re,itertools,math

def readEDL(path,seqKey,shotKey,FPS):
    edl_file = open( path, 'r')
    list = edl_file.readlines() 
    lines = filter(lambda x:not x.isspace(),list)
    edl_file.close()
    epiDict = parseEDL(lines,seqKey,shotKey,FPS)
    return epiDict

def getSource(path):
    edl_file = open( path, 'r')
    list = edl_file.readlines() 
    lines = filter(lambda x:not x.isspace(),list)
    edl_file.close()
    
    x = 0
    while x < len(list):
        val = list[x].strip()
        
        if re.search('FROM CLIP NAME',list[x]):
            if not re.search("EFFECTS",list[x-1]):
                tmp = list[x]
                break
        x = x + 1
        
    tmpSplit = tmp.split(" ")
    name = tmpSplit[-1]
    return name

def parseEDL(list,seqKey,shotKey,FPS):
    ioDict = {}
    codeList = [] 
    x = 0
    seqKey = seqKey.replace("#","[0-9]")
    shotKey = shotKey.replace("#","[0-9]")
    
    while x < len(list):
        val = list[x].strip()
        
        if re.search('FROM CLIP NAME',list[x]):
            if re.search(seqKey,list[x]):
                clipName = cleanCN(list[x].strip())
                code = re.search("[0-9][0-9][0-9]",str(list[x-1])).group()
                if code not in codeList:codeList.append(code)
                edlDict = createDict(list[x-1],FPS)
                ioDict[clipName] = edlDict
            else:
                if re.search("EFFECTS",list[x-1]):
                    clipName = cleanCN(list[x+1].strip())
                    code = re.search("[0-9][0-9][0-9]",str(list[x+1])).group()
                    if code not in codeList:codeList.append(code)
                    edlDict = createDict(list[x-2],FPS)
                    ioDict[clipName] = edlDict
                    
        if re.search('KEY CLIP NAME',list[x]):
            if re.search(seqKey,list[x]):
                clipName = cleanCN(list[x].strip())
                code = re.search("[0-9][0-9][0-9]",str(list[x-1])).group()
                if code not in codeList:codeList.append(code)
                edlDict = createDict(list[x-1],FPS)
                ioDict[clipName] = edlDict
                
        x = x + 1
    sDict = combineShots(ioDict,shotKey)
    shotDict = {}
     
    for s in sorted(sDict):
       tmpDict = {}
       startTC = 0
       seqDur = 0
       tmpList = sDict[s]
       shotName = s
       
       ## if the boards go out of order..  name_q####_s####-2.jpg name_q####_s####-3.jpg name_q####_s####-1.jpg
       tmpTCiList = [] 
       tmpSsList = []
       tmpSeList = []
       tmpTCoList = []
       
       for t in tmpList:
           shotStart = ioDict[t]['In']
           if shotStart not in tmpSsList:tmpSsList.append(shotStart)

           shotEnd = ioDict[t]['Out']
           if shotEnd not in tmpSeList:tmpSeList.append(shotEnd)

           tcIn = ioDict[t]['tcIn']
           if tcIn not in tmpTCiList:tmpTCiList.append(tcIn)
           
           tcOut = ioDict[t]['tcOut']       
           if tcOut not in tmpTCoList:tmpTCoList.append(tcOut)
        
       tmpSsList.sort()
       shotStart = tmpSsList[0]

       tmpSeList.sort()
       shotEnd = tmpSeList[-1]
                     
       tmpTCiList.sort()
       tcIn = tmpTCiList[0]
       
       tmpTCoList.sort()
       tcOut = tmpTCoList[-1]
       
#       tmpDict['shotStart'] = shotStart
#       tmpDict['shotEnd'] = shotEnd
       #shotDur = shotEnd - shotStart + 1
       
       shotDur = tcDiff(tcIn,tcOut,FPS)
       durFrames = TCtoFrames(shotDur,FPS)
       #shotDur = shotEnd - shotStart

       tmpDict['durFrames'] = durFrames
       tmpDict['shotDur'] = shotDur
       tmpDict['tcIn'] = tcIn
       tmpDict['tcOut'] = tcOut
       
       shotDict[shotName] = tmpDict
    
    epiDict = getSeq(shotDict,seqKey)
    return epiDict
        
def getSeq(shotDict,seqKey):

    sDict = {}
    tmpDict = {}
    seq = shotDict.keys()
    seqList = []
    seqKey = seqKey.replace("#","[0-9]")
    
    for s in seq:
        tmpSeqName = re.search(seqKey,s).group()
        nSplit = s.split(str(tmpSeqName))
        seqName = nSplit[0] + str(tmpSeqName)
        if seqName not in seqList:
            seqList.append(seqName)
    seqList.sort()
    
    for s in seqList:
        sDict = {}
        for key in sorted(shotDict.iteritems()):
            if re.search(s,key[0]):
                sDict[key[0]] = shotDict[key[0]]
        tmpDict[s] = sDict
    
    
    for x in sorted(tmpDict):
        seqStart = 0
        for y in sorted(tmpDict[x]):
#            print tmpDict[x][y]
#            if tmpDict[x][y]['tcIn'] == "00:00:00:00":
#                break
#            else:
            seqEnd = seqStart + tmpDict[x][y]['durFrames'] -1
            tmpDict[x][y]['seqStart'] = seqStart
            tmpDict[x][y]['seqEnd'] = seqEnd
            seqStart = seqEnd + 1
    
    return tmpDict

def combineShots(ioDict,shotKey):

    tmpDict = {}
    shots = ioDict.keys()
    shotList = []

    shotKey = shotKey.replace("#","[0-9]")

    for sh in shots:
        if re.search(shotKey,sh):
            tmpShotName = re.search(shotKey,sh).group()
            nSplit = sh.split(str(tmpShotName))
            shotName = nSplit[0] + str(tmpShotName)
            if shotName not in shotList:
                shotList.append(shotName) 

    for shot in shotList:
        if shot != "":
            tmpList = []
            for key in sorted(ioDict.iteritems()):
                if re.search(shot,key[0]):
                    tmpList.append(key[0])
            tmpDict[shot] = tmpList
    return tmpDict

def stripVal(value):
    try:
        value = value.strip(" ")
        value = value.strip("\n")
        value = value.strip("\r")
        return value
    except:
        pass
    
def TCtoFrames(TC,FPS):
    tcSplit = TC.split(":")
    HH = int(tcSplit[0])
    MM = int(tcSplit[1])
    SS = int(tcSplit[2])               
    FF = int(tcSplit[3])
    
    ffFrames = FF
    ssFrames = SS * FPS
    mmFrames = MM * 60 * FPS
    hhFrames = HH * 60 * 60 * FPS
    
    return ffFrames + ssFrames + mmFrames + hhFrames
    
def stripTC(line):
    tmpList = line.split(" ")
    tmpList = [x for x in tmpList if x != ""]
    return tmpList

def createDict(list,FPS):
    edlDict = {}
    tmpList = stripTC(list)
    if re.search("[0-9][0-9][0-9]",tmpList[4]):
        edlDict['effect'] = int(tmpList[4])
    edlDict['In'] = TCtoFrames(stripVal(tmpList[-2]),FPS)
    edlDict['tcIn'] = stripVal(tmpList[-2])
    edlDict['Out'] = TCtoFrames(stripVal(tmpList[-1]),FPS)
    edlDict['tcOut'] = stripVal(tmpList[-1])
    return edlDict
    
def cleanCN(l):
    clipSplit = l.split(":")
    clipName = clipSplit[-1]
    clipName = stripVal(clipSplit[-1])
    return clipName                

def frames_to_msTC(fps,frames):
    int_framerate = int(fps)
    HH = (frames / (3600*int_framerate))
    MM = (frames%(3600*int_framerate))/(60*int_framerate)
    SS = ((frames%(3600*int_framerate))%(60*int_framerate))/int_framerate
    
    MSplit = str(frames/float(int_framerate)).split(".")
    MS =  float("." + MSplit[-1])*1000
    return '%02d:%02d:%02d.%03d' % (HH,MM,SS,MS)

def frames_to_timecode(frames,fps):
    return '{0:02d}:{1:02d}:{2:02d}:{3:02d}'.format(frames / (3600*fps),frames / (60*fps) % 60,frames / fps % 60,frames % fps)

def tcDiff(tc1,tc2,fps):
    frameDif = TCtoFrames(tc2,fps) - TCtoFrames(tc1,fps)
    return frames_to_timecode(frameDif,fps)
    
#tcDiff("00:00:04:22","00:00:10:19",24)
#frames_to_msTC("24",45)

'''
seqKey = "sq###"
shotKey = "sh###"
FPS = 24
edlPath = "/Users/m2film/Dropbox/EDL/LOCB22_ANIMATC_M2_130417_SEQ10.edl"
#edlPath = 'U:/dsCore/tools/EDL/LOCB22_ANIMATC_M2_130417_SEQ10.edl'
readEDL(edlPath,seqKey,shotKey,FPS)
'''