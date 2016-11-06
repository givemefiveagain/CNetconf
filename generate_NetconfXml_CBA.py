#!/usr/bin/env python2
#-*-encoding:utf-8-*-

### <-----------------------------------------------------------------------------------> ###
#       welcome to use this script
#       This script is used to generate and execute CBA Netconf xml, and then check result  #
#       ./generate_NetconfXml_CBA.py snmpSet [-u|-d|] Moname attribute1 value1 ... ...      #
#       ./generate_NetconfXml_CBA.py operation Moname attribute1 value1 ... ...             #
#       author: eyuyany (Jenny Yu, CBC/XYD/D)                                               #
#       Version: v1                                                                         #
#       Date:16th Apr, 2014                                                                 #
### <------------------------------------------------------------------------------------> ###
## remove attributes which contain DataStatus sting such as ss7IsupItuNodeConnectionDataStatus in date 17th Mar.
## determine the delete,update,create for option -d, -u ,none in SnmpSet command line in date 17th Mar
## Get attributes of Mo table from MGC mim file , 19th Mar
## usage is /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet Moname MoId create attrib1 value1 attrib2 value2
## analyze the codecs attributes of MoSipprofile and MoMediaGateways in date 25th Mar
## '''sipProfileCodecs g711mLaw+g711aLaw+g729a+g7231+gsmEfr+amr+dtmfToneRelay+g72632+g72624+comfortNoise+clearMode+t38fax'''
## abstract from SipProfile, create SipProfileGroup1 and SipProfileGroup2 in dependence of input attribute in date 25th Mar
### extra the netconf xml three parts : rpc_mf, mf_mo, mo_attrib 
## get the ecim key from get mgc all configuration result, the ecim key is used for merge and delete operation. on 8th Apr.
### remove restricted attribute from input arguments on date 8th Apr.
### swith the type from integer to enum for some special attribute on date 8th Apr.
### change before process to adapt MoSipProfile on date 9th Apr.
### MoH248 cannot be created, just can be merged. swith operation type from create to merge for this kind of mo. on date 10th Apr
### create xml for Action such as activateBNumberAction,configSs7Action on date 15th Apr
##  snmpSet -u MoRadiusAccountingServer acctRadiusServerName 'radius'  acctRadiusServerAction eUnlocking, executed fail.
### using get mo instead of geting all

 

import xml.etree.ElementTree as ET
import re,os,getopt,sys

Element_Dict = {'rpc':{'message-id':"1",'xmlns':"urn:ietf:params:xml:ns:netconf:base:1.0"},
		'edit-config':{},
		'target':{},
		'running':{},
		'config':{'xmlns:xc':"urn:ietf:params:xml:ns:netconf:base:1.0"},
		'ManagedElement':{'xmlns':"urn:com:ericsson:ecim:ComTop"},
		'ManagedFunction':{'xmlns':"urn:com:ericsson:ecim:ManagedFunction"},
                'action':{'xmlns':"urn:com:ericsson:ecim:1.0"},
		'filter':{'type':"subtree"}
				}
attribute_Restricted = {'MoRouteAnalysis':['routeAnalysisRoutingCase','routeAnalysisTimeCategoryForRouting'],
                        'MoRouteAnalysisRoute':['routeAnalysisRoutingCase','routeAnalysisTimeCategoryForRouting','routeAnalysisRoutePriority','routeAnalysisResourceGroupIdentity'],
                        'MoSipProfile':['sipProfileName'],				
                        'MoBNumberPreAnalysis':['bNumberPreAnalysisOrigin','bNumberPreAnalysisNumberingPlan','bNumberPreAnalysisType','bNumberPreAnalysisAdditionalInfo'],
                        'MoBNumberAnalysis':['bNumberAnalysisOriginForAnalysis','bNumberAnalysisDialedNumber']
                       }
attribute_int2enum = {'sipProfileDiversionType':{'0':'eDiversionHeader', '1':'eHistoryInfoHeader'}}
JustOneInstanceMo = ['MoH248','MoAccountingConfiguration','MoSip','MoMgcf']
ActionMo = {'MoMgcf':['activateANumberAction', 'activateANumberPreAction', 'activateBNumberAction', 'activateBNumberPreAction',
                      'activateRouteAction', 'activateRouteAnalysisRouteAction', 'configSs7Action', 'restartSs7ConfigAction'],
            'MoMgDevice':['forcedLockingAction','gracefulLockingAction','unlockingAction','blockTimeSlotsAction',
                          'unblockTimeSlotsAction','resetTimeSlotsAction','auditDeviceAction'],
            'MoMediaGateway':['forcedLockingAction','gracefulLockingAction','unlockingAction']
           }


xml_head = '''
<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
<capabilities>
        <capability>urn:ietf:params:netconf:base:1.0</capability>
</capabilities>
</hello>
]]>]]>

<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="19" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
'''				

xml_tail = '''
</rpc>
]]>]]>


<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="19" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
<close-session/>
</rpc>
]]>]]>
'''			

xml_getall = '''
        <get-config>
                <source>
                        <running/>
                </source>
                <filter type="subtree">
                        <ManagedElement xmlns="urn:com:ericsson:ecim:ComTop">
                                <managedElementId>1</managedElementId>
                                <ManagedFunction xmlns="urn:com:ericsson:ecim:ManagedFunction">
                                        <managedFunctionId>1</managedFunctionId>
                                </ManagedFunction>
                        </ManagedElement>
                </filter>
        </get-config>
'''

def read_file(filename):
    f = open(filename,"r")
    content = f.read()
    f.close()
    return content
	
def execCmd(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text	
	
def search_elem(elem,list):
    if elem in list:
        return list.index(elem)
    else:
        return -1

def remove_staus(attri_list):
    length = len(attri_list)
    search_status = "[^\s]*(?:TableRowStatus|DataStatus)"
    pattern_status = re.compile(search_status)
    i = 0
    while i < length -1:
        if pattern_status.findall(attri_list[i]) :
            attri_list.remove(attri_list[i])
            attri_list.remove(attri_list[i])
            length = length - 2
        else:
            i = i + 2
    return attri_list

def split_codecs(attri_list):		

    length = len(attri_list)
    search_codecs = "[^\s]*Codecs"
    pattern_codecs = re.compile(search_codecs)
    i = 0
    first_match = True
    while i < length -1:
        if pattern_codecs.findall(attri_list[i]) and first_match == True:
            attrib_name = attri_list[i]
            attrib_val = attri_list[i+1]
            attri_list.remove(attri_list[i])
            attri_list.remove(attri_list[i])
            first_match = False
            lcodecs = attrib_val.split('+')
            for codec in lcodecs :
                attri_list.append(attrib_name)
                attri_list.append(codec)
        else:
            i = i + 2
    return attri_list


def Transform_Tag(tag):
    if (tag.find("Mo",0)==0):
        new_name = tag[2].lower()+tag[3:]+'Id'
    else:	
	new_name = tag[0].lower()+tag[1:]+'Id'
    return new_name
		

def Remove_RestrictedAttrib(mo_name, attrs_list):
    length = len(attrs_list)
    i = 0
    if mo_name in attribute_Restricted:
        while i < length-1 :
            if attrs_list[i] in attribute_Restricted[mo_name]:
                attrs_list.remove(attrs_list[i])
                attrs_list.remove(attrs_list[i])
                length = length -2
            else:
                i = i + 2

    return attrs_list 

def SwitchType_int2enum( attrs_list ):
    length = len(attrs_list)
    i = 0
    while i < length:
        if attrs_list[i] in attribute_int2enum:
           enum_value = attribute_int2enum[attrs_list[i]]
           if attrs_list[i+1] in enum_value:
               attrs_list[i+1] = enum_value[attrs_list[i+1]]
               break
        else:
            i = i +2
    return attrs_list 


def GetTableAttrib(root,table_name):
    attrib_list = []
    for child in root:
        if child.tag == 'mim' :
           for node in child :
               if node.tag == "class" and node.attrib == {'name': table_name}:
                   for attribute in node :
                       if attribute.tag == "attribute":
                           	attrib_list.append(attribute.attrib['name'])

    return attrib_list

def construct_edit_config_me():
    root_config = ET.Element('edit-config')
    target = ET.SubElement(root_config, "target")
    running = ET.SubElement(target, "running")
    config = ET.SubElement(edit_config, "config",Element_Dict['config'])
    return (root_config,config)

def construct_action_me():
    root_action = ET.Element('action',Element_Dict['action'])
    data = ET.SubElement(root_action, "data")
    return (root_action,data)

def construct_get_config_me():
    get_config = ET.Element('get-config')
    source = ET.SubElement(get_config, "source")
    running = ET.SubElement(source, "running")
    filter = ET.SubElement(get_config, "filter",Element_Dict['filter'])
    return (get_config,filter)	
	
def construct_me_mf():
    ManagedElement = ET.Element('ManagedElement',Element_Dict['ManagedElement'])
    ManagedElementId = ET.SubElement(ManagedElement, Transform_Tag("ManagedElement"))
    ManagedElementId.text = '1'
    ManagedFunction = ET.SubElement(ManagedElement, "ManagedFunction",Element_Dict['ManagedFunction'])
    ManagedFunctionId = ET.SubElement(ManagedFunction, Transform_Tag("ManagedFunction"))
    ManagedFunctionId.text = '1'
    return (ManagedElement,ManagedFunction)

def extra_mf_mo_layers( moname , mim_content ):

    # search the relationship parent and child , and save the search result
    search_keys = ''' <containment>\s*<parent>\s*<hasClass name="(\w*)">\s*<mimName>\w*</mimName>\s*</hasClass>\s*</parent>\s*<child>\s*<hasClass name="(\w*)">\s*<mimName>\w*</mimName>\s*</hasClass>\s*<cardinality>\s*<min>\d*</min>\s*<max>\d*</max>\s*</cardinality>\s*</child>\s*</containment>'''
    pattern = re.compile(search_keys)
    lists = pattern.findall(mim_content)
    # find the layers from mo name to ManagedFunction and return the layer list 
    parents = []
    children = []
    length = len(lists)
    for i in range(0,length):
        parents.append( lists[i][0] )
        children.append( lists[i][1])
    mo_mf_layers =[moname]
    pindex =  search_elem(moname,children) 
    parent = parents[pindex]
    while (pindex != -1) and (parent != "ManagedFunction") :
        mo_mf_layers.append(parent)
        pindex = search_elem(parent,children) 
        parent = parents[pindex]
    if parent == "ManagedFunction":
        mo_mf_layers.append(parent)
		
    return mo_mf_layers	
	
	
def construct_mf_mo(mo_mf_layers):
    #construct xml format for mo_mf_layers
    length = len(mo_mf_layers)
    mf_mo_root=ET.Element(mo_mf_layers[length-2])
    mo_Id = ET.SubElement(mf_mo_root, Transform_Tag( mo_mf_layers[length-2]))
    mo_Id.text = '1'

    parent = mf_mo_root
    for i in range(length-3,0,-1):
         child = ET.SubElement(parent, mo_mf_layers[i])
         childId = ET.SubElement(child, Transform_Tag( mo_mf_layers[i]))
         childId.text = '1'
         parent = child	
    return (mf_mo_root,parent)


def construct_mo_attrib(mo_name,moId,operation_type,attribs_list):
    mo_root=ET.Element(mo_name)
    mo_Id = ET.SubElement(mo_root, Transform_Tag(mo_name))
    if moId:
       mo_Id.text = moId
    else:
       mo_Id.text = '1'
    if operation_type == 'action' :
        ET.SubElement(mo_root,attribs_list[0])
    else :
        mo_root.attrib['operation'] = operation_type
        i = 0
        while i < len( attribs_list )-1:
            subelem = ET.SubElement(mo_root,attribs_list[i])
	    subelem.text = attribs_list[i+1]
 	    i = i + 2
    return mo_root	  

def SplitMoSipProfileToGroups(fname, moName, attrib_list):
    # this function is for MoSipProfile
    tree_mimfile = ET.parse(fname)
    root_mimfile = tree_mimfile.getroot()	
    attribOfMoSipProfileGroup1 = GetTableAttrib(root_mimfile,'MoSipProfileGroup1')	
    attribOfMoSipProfileGroup2 = GetTableAttrib(root_mimfile,'MoSipProfileGroup2')	
    length = len(attrib_list)
    i = 0
    lattri_group1 = []
    lattri_group2 = []
    groups = []
    while i < length-1 :
        if attrib_list[i] in attribOfMoSipProfileGroup1 :
            lattri_group1.append(attrib_list[i])
            lattri_group1.append(attrib_list[i+1])				
        if attrib_list[i] in attribOfMoSipProfileGroup2 :
            lattri_group2.append(attrib_list[i])
            lattri_group2.append(attrib_list[i+1])					
        i = i + 2
    if len(lattri_group1) >= 2 and lattri_group1[len(lattri_group1)-1] != 'sipProfileName' :  # lattri_group1 is not empty
	groups = ['MoSipProfileGroup1', lattri_group1]
    if len(lattri_group2) >=2 and lattri_group2[len(lattri_group2)-1 ] != 'sipProfileName' :
        groups.append('MoSipProfileGroup2')
        groups.append(lattri_group2)
    return groups

def handle_argvs(first_index ):
    '''  output is :operation_type,MOname,MoId,attribs_list  
        snmpSet usage is /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet [-u|-d] Moname [MoId] attrib1 value1 attrib2 value2 ... ...
 						 /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet Moname action_type
        netconf usage is /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath Moname [create|merge|delete] attrib1 value1 attrib2 value2 ... ...
                         /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath Moname [MoId] action_type
        Get all:
		                /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath getall
    '''
    attri_list = sys.argv
    operation_type = MOname = MoId = attribs_list =None
    attribs_list = attri_list[start_index+3:]
    if  re.findall(r'^snmp\s*',attri_list[start_index]): #snmpSet cmd
        if attri_list[start_index+1] == '-d':
            operation_type = 'delete'
            MOname = attri_list[start_index+2]
        elif attri_list[start_index+1] == '-u':		
            operation_type = 'merge'
            MOname = attri_list[start_index+2]			
        else:
            operation_type = 'create'	
            MOname = attri_list[start_index+1]	
            if re.findall(r'^\d',attri_list[start_index+2]) :  #input arguments contain MoId.
                MoId = attri_list[start_index+2]
            else :
                attribs_list = 	attri_list[start_index+2:]	
            if (MOname in JustOneInstanceMo) and ( len(attribs_list) > 1 ):
                operation_type = 'merge'
            if attribs_list[0] in ActionMo[MOname] :
                operation_type = 'action' 			
    elif re.findall(r'^Mo\s*',attri_list[start_index]): # for netconf cmd
        MOname = attri_list[start_index]
        operation_type = attri_list[start_index+1]  #create or merge or delete
        attribs_list = attri_list[start_index+2:]
        if re.findall(r'^\d',operation_type):  #contain MoId for action
            MoId = operation_type 
            operation_type = 'action'
        elif operation_type in ActionMo[MOname] : #no MoId 
            operation_type = 'action'
            MoId = '1'
            attribs_list = attri_list[start_index+1]		    
    elif re.findall(r'^getall',attri_list[start_index]):   
        operation_type = 'getall'
    attribs_list = split_codecs(attribs_list) #split codecs.
    attribs_list = SwitchType_int2enum(attribs_list) #switch type from int to enum
    return (operation_type,MOname,MoId,attribs_list)
	
def construct_fxml(moName,moId,operation,attrs_list,content,Netconfxmldir):
    #construct the xml from rpc to attributes
    mo_mf_layers = extra_mf_mo_layers( moName , content )
    if operation == 'action':
       (root,first_child)= construct_action_me()
    else:
       (root,first_child)=construct_edit_config_me()
    (ManagedElement,ManagedFunction)=construct_me_mf()
    (mf_mo_root,mo_parent) = construct_mf_mo(mo_mf_layers)
    if not moId:  # in condition MoId is null
		(MaxMatchId, MaxId) = GetEcimKey( moName,operation,attrs_list)
        if operation_type == 'create':
            moId = str(MaxId + 1)
        elif operation_type == 'merge' or operation_type == 'delete':
            moId = str(MaxMatchId)	
    mo_root = construct_mo_attrib(moName,moId,operation,attrs_list)
    print 'mo_root********',ET.tostring(mo_root)
    mo_parent.append(mo_root)
    ManagedFunction.append(mf_mo_root)
    first_child.append(ManagedElement)
    rpc_attib_string = ET.tostring(root)
    return rpc_attib_string


def read_mimfile():
    fmim = execCmd('find /cluster/storage/system/software/coremw/repository/ -name MGC_mp.xml')
    content = read_file(fmim[:-1])
    tree_mimfile = ET.parse(fmim[:-1])
    root_mimfile = tree_mimfile.getroot()
    return (fmim[:-1], content)

def tupleswitchtolist(MOinGetAll_tuple):
    length = len(MOinGetAll_tuple)
    MOinGetAll_list = []
    for i in range( 0, length):
        MOinGetAll_list.append(MOinGetAll_tuple[i][0])
        MOinGetAll_list.append(MOinGetAll_tuple[i][1])
    return MOinGetAll_list


def writexml( xml_body,Netconfxmldir,Moname='netconfXml' ,method = 'w',resultfile='netconfXml.result' ):

    xml_str = xml_head + xml_body + xml_tail
    xml_fname = Netconfxmldir + '/' + Moname+'.xml'
    print xml_str
    f = open ( xml_fname ,method)
    f.write(xml_str)
    f.close()
    result = execCmd('/opt/com/bin/netconf < '+ Moname+'.xml' )
    if Moname=='netconfXml':
        ok_num = re.findall(r'<ok/>',result)
        print result
        if len(ok_num) == 2 :
           print 'configured OK'
        else :
           print 'configured fail!!!!'
    f = open(Netconfxmldir + '/' + resultfile,method)
    f.write(result)
    f.close()

def GetMoConfig(moname):
    '''  Get all instance in the assigned mo before determin the ECIM Key'''	
    (edit_config, filter) = construct_edit_config_me()
    (me,mf) = construct_me_mf()
    (mf_mo_root,mo_parent) = construct_mf_mo(mo_mf_layers)
    filter.append(me)
	mf.append(mf_mo_root)
    ET.SubElement(mo_parent, moName)
    edit_config_moname_string = ET.tostring(edit_config)
	MoConfigResult = 'GetMoConfig.result'
    writexml( edit_config_moname_string, Moname='GetMoConfig',resultfile=MoConfigResult)
	MoConfiguration = read_file(MoConfigResult)
	return MoConfiguration
	
def GetEcimKey( moName ,operation_type, attrs_input ):
    ''' get ecim key for replace operation.
	''' 
	content = GetMoConfig(moName)
    search_mo = '<'+moName+'>([\d\w\s\D]*?)</'+moName+'>'
    pattern = re.compile(search_mo)
    MOs = pattern.findall(content) ## find instance of MO
    attr_pattern = '<(\w*)>([^\s]*)</\w*>'
    pattern = re.compile(attr_pattern)
    MaxId = 0
    MaxMatch = 0
    MaxCount = 0
    mo_num = len(MOs)
    if mo_num == 1:
        attrs_mo = pattern.findall(MOs[0])
        attrs_mo_list = tupleswitchtolist(attrs_mo)
        ecim_attrib = Transform_Tag(moName)
        if ecim_attrib in attrs_mo_list:
           ecim_id_in_list  = attrs_mo_list.index(ecim_attrib) + 1
           MaxMatch = MaxId = attrs_mo_list[ecim_id_in_list]
    elif mo_num > 1:    
        for mo_index in range(0,mo_num):
            attrs_mo = pattern.findall(MOs[mo_index])
            attrs_mo_list = tupleswitchtolist(attrs_mo)
            count = i = current_id = 0
            while i < len(attrs_input) -1:
                attrib_index = search_elem(attrs_input[i],attrs_mo_list)
                value_index = search_elem( attrs_input[i+1],attrs_mo_list )
                current_id = attrs_mo_list[1]
                if (attrib_index != -1) and (value_index != -1) and (attrib_index == value_index -1 ):
                    count = count +1
                i = i+2
            if MaxCount < count:
                MaxMatch = attrs_mo_list[1]
                MaxCount = count
	    if MaxId < current_id :
	        MaxId = current_id
    attribs_list = remove_staus(attrs_input)  # remove DataStatus and RowStatus
    if operation_type != 'create':
	    attribs_list = Remove_RestrictedAttrib(MOname, attribs_list)	
    print MaxMatch,MaxId
    return (int(MaxMatch),int(MaxId))

def handleSipProfileGroups(ProfileGroups,operation_type,MoId,content, Netconfxmldir):
    i = 0
    while i < len(ProfileGroups)-1:
        MOname = ProfileGroups[i]
        attribs_list = ProfileGroups[i+1]
        if not MoId:  # in condition MoId is null
		    (MaxMatchId, MaxId) = GetEcimKey( moName,operation_type,attribs_list)
            if operation_type == 'create':
                MoId = str(MaxId + 1)
            elif operation_type == 'merge' or operation_type == 'delete':
                MoId = str(MaxMatchId)		
        xml = construct_fxml(MOname,MoId,operation_type,attribs_list,content, Netconfxmldir)
		writexml(xml,Netconfxmldir)
        i = i + 2

	
if __name__ == '__main__':

    '''snmpSet usage is /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet [-u|-d] Moname [MoId] attrib1 value1 attrib2 value2 ... ...
        initial create operation is : /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet  Moname MoId attrib1 value1 attrib2 value2 ... ...
        create during FT or RT opearion is : /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet -d Moname attrib1 value1 attrib2 value2 ... ...
        merge opearion is : /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet -u Moname attrib1 value1 attrib2 value2 ... ...
        delete opearion is : /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet -d Moname attrib1 value1 attrib2 value2 ... ...
        Action operation is : /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath snmpSet Moname Action_Type
                              /NetconfScriptPath/AutoRunNetconf.py /NetconfScriptPath Moname Action_Type
    '''
    length_argv = len(sys.argv)
    start_index = 2                                    # the first index to read the input useful arguments.
    Netconfxmldir = sys.argv[start_index - 1]          # the directory to store generated netconf xml files
    (fmim, content) = read_mimfile()                   # find file MGC_mp.xml, and read the content of it.
    (operation_type,MOname,MoId,attribs_list) = handle_argvs( start_index )    # reomve status, and restricted attributes, switch type from int to enum for some especial attribute
    print 'operation_type,MOname,MoId,attribs_list',operation_type,MOname,MoId,attribs_list
    if operation_type == 'create' or operation_type == 'merge' or operation_type == 'delete' or operation_type == 'action' :
        if MOname == 'MoSipProfile' :
            profilegroups = SplitMoSipProfileToGroups(fmim, MOname, attribs_list)
            handleSipProfileGroups(profilegroups,operation_type,MoId,content, Netconfxmldir)
        else : # other MOs
 	        xml = construct_fxml(MOname,MoId,operation_type,attribs_list,content, Netconfxmldir)
            writexml(xml,Netconfxmldir)
    elif operation_type == 'getall' :
        writexml(xml_getall,Netconfxmldir,'GetMGCAllConfig')		
