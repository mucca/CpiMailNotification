from Products.CMFCore.CMFCorePermissions import ManagePortal, View
from Products.CpiMailNotification.config import *

from Products.Archetypes.debug import log
from StringIO import StringIO


def install(self):
    """  """

    out = StringIO()

    from Products.CpiMailNotification import MailNotificationTool
    
    if not hasattr(self, 'mailnotification_tool'):
        addTool = self.manage_addProduct[PROJECT_NAME].manage_addTool
        addTool('MailNotificationTool')
        out.write('MailNotificationTool tool installed')

    return out.getvalue()


configlets = (
    {  'id' : 'uego_configuration'
     , 'name' : 'Support System configuration'
     , 'action' : 'string:${portal_url}/prefs_manage_uego'
     , 'category' : 'Products'
     , 'appId' : PROJECT_NAME
     , 'permission' : ManagePortal
     , 'imageUrl' : 'IGNIcon.gif'
     },)


def addConfiglets(self, out):
    configTool = getToolByName(self, 'portal_controlpanel', None)
    if configTool:
        for conf in configlets:
            out.write('Adding configlet %s\n' % conf['id'])
            configTool.registerConfiglet(**conf)



#############
# UNINSTALL #
#############

def uninstall(self):

    out=StringIO()

    ## remove the product from the configlet
    #removeConfiglets(self, out)

    return out.getvalue()

