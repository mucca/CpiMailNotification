from Products.CMFCore import utils, CMFCorePermissions, DirectoryView
from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory
from Products.Archetypes.public import *
from Products.Archetypes.debug import log
import Patches

from config import *

#registerDirectory("skins", GLOBALS) 
from AccessControl import ModuleSecurityInfo
ModuleSecurityInfo('Products.SupportSystem').declarePublic('debug')

def initialize(context):

    import MailNotificationTool

    ToolInit(meta_type = "MailNotification Tool",
             tools = (MailNotificationTool.MailNotificationTool,),
             icon="mailnotification_tool.gif").initialize(context)




