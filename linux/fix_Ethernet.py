import os, subprocess

import xml.etree.cElementTree as etree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = etree.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(str(rough_string))
    return reparsed.toprettyxml(indent="  ")

def load(path):
    '''Checks if the path exists and it has any data
       returns parse xml file
    '''
    if os.path.exists(path) or os.stat(path).st_size:
        try: return etree.parse(path)
        except  Exception as e:
            print 'ERROR READING XML:%s\nERROR:%s' % (path, e)
    else:
        print 'Couldnt find %s' % (path)

def save(path, elem):
    file = open(path, 'w')
    for line in prettify(elem).split('\n'):
        if line.strip(): file.write('%s\n' % line)
    file.close()




ipdict = {'rp09': ('0.179', '00:19:B9:E6:18:CD'), 
                'rp10': '0.180', 
                'rp11': '0.181', 
                'rp12': '0.182',
                'rp13': '0.183',
                'rp14': '0.184', 
                'rp15': '0.185', 
                'rp16': '0.186',
                'rp17': '0.187', 
                'rp18': '0.188', 
                'rp19': '0.189', 
                'rp20': '0.190', 
                'rp21': '0.191', 
                'rp22': '0.192', 
                'rp23': '0.193',
                'rp24': '0.194', 
                'rp25': '0.195', 
                'rp26': '0.196', 
                'rp27': '0.197', 
                'rp28': '0.198', 
                'rp29': '0.199', 
                'rp30': '0.200', 
                'rp32': '0.167', 
                'rp33': '0.168',
                'rp34': '0.169',
                'rp35': '0.174',
                'vfx000':'0.106',
                'vfx101':'0.124',
                'vfx102':'0.125',
                'vfx103':'0.126',
                'vfx104':'0.127',
                'vfx105':'0.128',
                'vfx106':'0.134',
                'vfx107':'0.135',
                'vfx108':'0.136',
                'vfx109':'0.137',
                'vfx110':'0.138',
                'vfx111':'0.139',
                'vfx112':'0.140',
                'vfx113':'0.141',
                'vfx114':'0.142',
                'vfx115':'0.143',
                'vfx116':'0.144',
                'vfx117':'0.145',
                'vfx118':'0.146',
                'vfx119':'0.147',
                'vfx120':'0.148',
                'vfx121':'0.149',
                'vfx122':'0.83',
                'vfx123':'0.84',
                'vfx124':'0.85',
                'vfx125':'0.86',
                'vfx126':'0.87',
                'vfx127':'0.88',
                'vfx128':'0.89'
                 }

def copy(src, dst):
    return process('sudo cp %s %s' % (src, dst)).communicate()[0]

def createDict(ipdict):
    for i in range(9, 31):
        ipdict['rp%02d' % (i)] = '0.%d' % (180 + (i -10))
    return ipdict
    
def get_hostname():
    return os.environ['HOSTNAME']

def restart_Ethernet():
    return process("sudo /etc/init.d/network restart").communicate()[0]

def get_hardwareID():
    return process("ifconfig | grep eth | awk '{ print $5}'").communicate()[0].rstrip()

def get_deviceName():
    return process("ifconfig | grep eth | awk '{ print $1}'").communicate()[0].rstrip()
    
def process(cmd_line):
    '''
    Using subprocess.Popen to start a new process
    Returning the process when its started.
    '''
    proc = subprocess.Popen(cmd_line, 
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        )
    return proc

def write_Ifcfg(ipdict):
    hostname = get_hostname()
    hardwareid = get_hardwareID()
    devicename = get_deviceName()
    path = '/dsGlobal/dsCore/tools/linux/ifcfg-%s' %(hostname)
    print hostname
    print hardwareid
    print devicename
    print path
    file = open(path, 'w')
    file.write('NAME=%s\n' % hostname)
    file.write('TYPE=Ethernet\n')
    file.write('BOOTPROTO=none\n')
    file.write('DOMAIN=duckling.dk\n')
    file.write('DEFROUTE=yes\n')
    file.write('IPV4_FAILURE_FATAL=yes\n')
    file.write('IPV6INIT=no\n')
    file.write('ONBOOT=yes\n')
    file.write('HWADDR=%s\n' % hardwareid)
    file.write('DNS1=192.168.1.229\n')
    file.write('PEERROUTES=yes\n')
    file.write('DEVICE=%s\n' % devicename)
    file.write('USERCTL=no\n')
    file.write('IPADDR=192.168.%s\n' % (ipdict[str(hostname).lower()]))
    file.write('NETMASK=255.255.254.0\n')
    file.write('GATEWAY=192.168.1.1\n')
    file.close()
    
    return path

if __name__ == "__main__":
    serv = write_Ifcfg(ipdict)
    local = '/etc/sysconfig/network-scripts/ifcfg-%s' % get_hostname()
    copy(serv, local)
    restart_Ethernet()
    
    ### Begining on making a xml to control the script Stefan
    
    #path = '//vfx-data-server/dsGlobal/dsCore/tools/linux/ipconfig.xml'
    #path = '/dsGlobal/dsCore/tools/linux/ipconfig.xml'
    #"""root = etree.Element( 'root' )
    #elem = etree.SubElement(root, 'Rp12')
    #child = etree.SubElement(elem, 'device')
    #child.set('HWADDR', '00:19:B9:E3:54:25')
    #child = etree.SubElement(elem, 'device')
    #child.set('HWADDR', '00:1E:67:06:A5:35')
    #child.set('HWADDR', '00:1E:67:06:A5:35')
    #elem.set('IPADDR', '192.168.0.186')"""
    
    #save('//vfx-data-server/dsGlobal/dsCore/tools/linux/ipconfig.xml', root)
    #hmm = load(path).getroot()
    #for child in hmm.getiterator():
    #    print child.tag
    