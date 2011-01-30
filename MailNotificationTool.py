##############################################################################
#
#    Mail notification tool, a zope tool for managment of mail send on workflow state changes
#    Copyright (C) 2007 opencpi@cpiprogetti.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFCore.utils import UniqueObject
from OFS.Folder import Folder

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, package_home
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.DTMLMethod import DTMLMethod
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from AccessControl.SecurityManagement import newSecurityManager,noSecurityManager

from Products.CpiMailNotification.config import *

import os
import random
from Mailer import Mailer

import pdb
from Products.Archetypes.debug import log

def _addObject(self, ob):
    id = ob.getId()
    while hasattr(self, id):
        id = id+ str(random.randrange(0, 555))
    if not hasattr(self,'_objects'):
        self._objects=({},)

    setattr(self, id, ob)
    self._objects = self._objects + (
        {'id': id, 'meta_type': ob.meta_type},)

class MailNotificationTool(PloneBaseTool, UniqueObject, Folder):

    __implements__ = (PloneBaseTool.__implements__, Folder.__implements__)
    
    security = ClassSecurityInfo()

    #manage interfaces definition
    manage_mail = PageTemplateFile('www/manage_mail', globals())
    manage_mailer = PageTemplateFile('www/add_mailer', globals())
    
    manage_options = (
        {'label': 'Mail Notification Properties',
         'action': 'manage_mail'},
    ) + Folder.manage_options


    id = 'mailnotification_tool'
    meta_type = 'MailNotificationTool'
    title = 'MailNotificationTool'
    version = 2

    def addMailerFor(self, title, 
                                    selected_transition, 
                                    selected_workflow, 
                                    mail_from_expression, 
                                    mail_header_dtml, 
                                    mail_head_css_dtml,
                                    mail_body_dtml,
                                    message_id_expression=None, 
                                    in_replay_to_expression=None,
                                    mail_to_expression='',
                                    mail_to_list=[], 
                                    mail_to_roles=[], 
                                    mail_to_groups=[], 
                                    mail_cc_expression='', 
                                    mail_cc_list=[], 
                                    mail_cc_roles=[], 
                                    mail_cc_groups=[], 
                                    mail_ccn_expression='', 
                                    mail_ccn_list=[], 
                                    mail_ccn_roles=[], 
                                    mail_ccn_groups=[] ):
                                            
        if not (title and selected_transition and selected_workflow):
            raise Exception("Parameters title, selected_transition, selected_workflow cannot be None ")
        mailer = Mailer(title)
        
        mailer.editMailerForm(mail_from_expression, mail_header_dtml, mail_head_css_dtml, mail_body_dtml,
                                            message_id_expression,in_replay_to_expression,
                                            mail_to_expression, mail_to_list, mail_to_roles, mail_to_groups, 
                                            mail_cc_expression, mail_cc_list, mail_cc_roles, mail_cc_groups, 
                                            mail_ccn_expression, mail_ccn_list, mail_ccn_roles, mail_ccn_groups )
        
        # put insede the dictionary the object
        if not hasattr(self, selected_workflow):            
            _addObject(self, Folder(selected_workflow) )
        
        workflowFolder = getattr(self, selected_workflow)
        if not hasattr(workflowFolder, selected_transition):
            _addObject(getattr(self,selected_workflow), Folder(selected_transition) )        
        
        transitionFolder = getattr(workflowFolder , selected_transition)

        _addObject(transitionFolder, mailer )
        
    
    def manage_addMailerFor(self,title, selected_transition,selected_workflow, REQUEST=None):
        """ add a mailer for a specific transition on a specific mailer """
        if not title:
            raise Exception("You must specify an id")
        if not selected_transition:
            raise Exception("No transition spiecified")
        if not selected_workflow:
            raise Exception("No workflow spiecified")
        
        mailer = Mailer(title)

        # put insede the dictionary the object
        if not hasattr(self, selected_workflow):            
            _addObject(self, Folder(selected_workflow) )
        
        workflowFolder = getattr(self, selected_workflow)
            
        if not hasattr(workflowFolder, selected_transition):
            _addObject(getattr(self,selected_workflow), Folder(selected_transition) )
        
        transitionFolder = getattr(workflowFolder , selected_transition)
        
        _addObject(transitionFolder, mailer )
        
        if REQUEST:
            REQUEST.RESPONSE.redirect(transitionFolder.absolute_url() + "/" + title + "/edit_mailer?manage_tabs_message=Mailer+correctly+added" )
        
        
        return mailer
        
    def enter(self, something=None):
        pdb.set_trace()
    
    def getNotifiersForWorkFlow(self, workflow_id):
        if hasattr(self, workflow_id):
            wfMailersContainer = getattr(self, workflow_id)
            notifiersList = []
            for state in wfMailersContainer.getChildNodes():
                notifiersList += [ mailer for mailer in state.getChildNodes() if mailer._isMailer ]
            return notifiersList
        else:
            return []
            
    def getNotifiersForWorkFlowTransition(self, workflow_id, transition_id):
        if hasattr(self, workflow_id):
            wfMailersContainer = getattr(self, workflow_id)
            if hasattr(wfMailersContainer, transition_id):
                wfTransitionMailersContainer = getattr(wfMailersContainer, transition_id)
                notifiersList = []
                for mailer in wfTransitionMailersContainer.getChildNodes():
                    if mailer._isMailer:
                        notifiersList += [mailer]
                return notifiersList
                
        return []
    
    def hasNotifierForWorkFlowTransition(self, workflow_id, transition_id, notifier_id):
        notList = self.getNotifiersForWorkFlowTransition(workflow_id, transition_id)
        for notifier in notList:
            if notifier.id == notifier_id:
                return True
    
    def stateTransationNotify(self, stateChangeInfo):
        """ method called from the workflow patch to notify a transition """
        notifiersList = []
        if stateChangeInfo.transition:
            notifiersList = self.getNotifiersForWorkFlowTransition(stateChangeInfo.workflow.id, stateChangeInfo.transition.id)
        if not notifiersList:
            return
        for notifier in notifiersList:
            notifier.stateTransationNotify(stateChangeInfo)
            
    def getMemberEmailByUserId(self, userId):
        """ utility method to get email from a userid """
        try:
            userEmail = self.portal_membership.getMemberById(str(userId)).getProperty('email')
        except:
            return None
        return userEmail
        

    #######################################
    ## mail notification utility methods ##
    #######################################

    def getMailReceiversByLocalRoles(self, obj, local_roles=[]):
        """  utility method thad return a list of e-mails in base of a local_roles list on an object """
        receivers = []
        local_roles = set(local_roles)

        for user in obj.computeRoleMap():
            if local_roles.issubset(local_roles.intersection(set(user.get('local')))):
                if (obj.portal_membership.getMemberById(user.get('id')).getProperty('email')):
                    mTo = obj.portal_membership.getMemberById(user.get('id')).getProperty('email','')
                    receivers.append(mTo)
        return receivers

    def mailReceiversByRoles(self, obj, roles=[]):
        """  TODO """
        pass

    ## TODO actualy a member of n group receive n mails
    def getMailReceiversByGroups(self, obj, groups=[]):
        """ return list of e-mail of users in groups """
        receivers = []

        for group in groups:
            obj_groups = obj.acl_users.getGroupById(group)
            for user in obj_groups.getGroupMembers():
                if self.getMemberEmailByUserId(user.id):
                    mTo = self.getMemberEmailByUserId(user.id)
                    receivers.append(mTo)
        return receivers
      
InitializeClass(MailNotificationTool)