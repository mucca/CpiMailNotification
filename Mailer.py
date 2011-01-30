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


from OFS.SimpleItem import SimpleItem
from OFS.DTMLMethod import DTMLMethod
from AccessControl import ClassSecurityInfo
from Products.CMFCore import permissions
from Products.CMFCore.Expression import Expression
from Products.DCWorkflow.Expression import createExprContext
from Products.DCWorkflow.Expression import StateChangeInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CpiMailNotification.debug import log, warn
from socket import gaierror
import pdb
import sys, traceback
from threading import Thread


class SenderThread(Thread):
    def __init__(self, pMailHost, pMTo, pMFrom, pMCC, pMCCN, pMHeader, pMBodyFull, pOptions):
        Thread.__init__(self)
        self.gMailHost = pMailHost
        self.gMTo = pMTo
        self.gMFrom = pMFrom
        self.gMCC = pMCC
        self.gMCCN = pMCCN
        self.gMHeader = pMHeader
        self.gMBodyFull = pMBodyFull
        self.gOptions = pOptions

    def run(self):
        try:
            self.gMailHost.secureSend(self.gMBodyFull, 
                                                       self.gMTo,
                                                       self.gMFrom, 
                                                       self.gMHeader,
                                                       self.gMCC, self.gMCCN, "html",charset="utf-8", **self.gOptions)
            log("Mail succesfully sent by thread " + str(self))                                                       
        except:
            type, val, tb = sys.exc_info()
            traceback.print_exc(file=sys.stdout)
            warn("Mail cannot be sent : \nException type: %s \nException value: %s \nException tb: %s" % (type, val, tb) )
        

class Mailer(SimpleItem):
    """ Mailer class for CpiMailNotification """

    meta_type='simple mailer'
    #icon="mailnotification_tool.gif"
    _isMailer = True
    
    security = ClassSecurityInfo()
    security.declareObjectProtected(permissions.ManagePortal)

    edit_mailer = PageTemplateFile('www/edit_mailer', globals())
    manage_options = (
        {'label': 'Edit Mailer',
         'action': 'edit_mailer'},
    ) + SimpleItem.manage_options
    
    def __init__(self, id=None, initFromDict=None):
        """ Initialize instance's variables to store expression and list to resolve the receivers of notify mail """
        
        self.mail_from_expression = None
        self.message_id_expression = None   #Message-ID: <068.79073e66efd650441fb2d1b589c585d2@cpiprogetti.it>
        self.in_replay_to_expression = None    #In-Reply-To: <059.dc5d2233e00d1c4b46766a647f023c81@cpiprogetti.it>
        
        self.mail_to_expression = None
        self.mail_to_list = []
        self.mail_to_roles = []
        self.mail_to_groups = []

        self.mail_cc_expression = None
        self.mail_cc_list = []
        self.mail_cc_roles = []
        self.mail_cc_groups = []

        self.mail_ccn_expression = None
        self.mail_ccn_list = []
        self.mail_ccn_roles = []
        self.mail_ccn_groups = []
        
        self.mail_header_dtml = None
        self.mail_head_css_dtml = None
        self.mail_body_dtml = None
        
        self.id = id

    def getExpressionText(self, expression):
        try:
            text = expression.text
            return text
        except AttributeError:
            log(AttributeError)
            return ""

    def resolveRoles(self, stateChangeInfo, rolesSetToVerify):
        """ works with all types of roles and localroles only for users case... and don't work with groups localroles"""
        
        roles = self.plone_utils.getInheritedLocalRoles(stateChangeInfo.object)
        rolesSetToVerify = set(rolesSetToVerify)
        membersList = []
        for member in roles:        
            if self.acl_users.getUserById(member[0]):
                if rolesSetToVerify & ( set(member[1]) | set(self.acl_users.getUserById(member[0]).getRoles()) | set(stateChangeInfo.object.get_local_roles_for_userid(member[0]) )): 
                    
                    if member[0] not in membersList:
                        membersList.append(member[0])
        memberEmailList = []
        for member in membersList:
            email = self.mailnotification_tool.getMemberEmailByUserId(member)
            if email not in memberEmailList:
                memberEmailList.append(email)
        
        return memberEmailList

    def resolveGroups(self, groups=[]):
        return self._getMailReceiversByGroups(groups)

    def _getMailReceiversByGroups(self, groups=[]):
        """  """
        receivers = []

        for group in groups:
            obj_groups = self.acl_users.getGroupById(group)
            for user in obj_groups.getGroupMembers():
                if user.getProperty('email'):
                    mTo = user.getProperty('email','')
                    receivers.append(mTo)
        return receivers
    
    def _resolveMailTOAddreses(self,econtext, stateChangeInfo):
        mTo = []
        if self.mail_to_expression:
            mTo += self.mail_to_expression(econtext)
        mTo += self.mail_to_list 
        mTo += self.resolveRoles(stateChangeInfo, self.mail_to_roles)
        mTo += self.resolveGroups(self.mail_to_groups)
        return mTo
    
    def _resolveMailCCAddreses(self, econtext, stateChangeInfo):
        mCc= []
        if self.mail_cc_expression:
            mCc += self.mail_cc_expression(econtext)
        mCc += self.mail_cc_list 
        mCc += self.resolveRoles( stateChangeInfo , self.mail_cc_roles)
        mCc += self.resolveGroups(self.mail_cc_groups)
        return mCc
        
    def _resolveMailCCNAddreses(self, econtext, stateChangeInfo):
        mCcn = []
        if self.mail_ccn_expression:
            mCcn += self.mail_ccn_expression(econtext)
        mCcn += self.mail_to_list 
        mCcn += self.resolveRoles( stateChangeInfo , self.mail_ccn_roles)
        mCcn += self.resolveGroups(self.mail_ccn_groups)
        return mCcn
        
    def _resolveMailFromAddress(self, econtext):
        return self.mail_from_expression(econtext)
        
    def stateTransationNotify(self, stateChangeInfo):
        econtext = createExprContext(stateChangeInfo)
        
        mFROM = self._resolveMailFromAddress(econtext)
        mTO = self._resolveMailTOAddreses(econtext, stateChangeInfo)
        mCC = self._resolveMailCCAddreses(econtext, stateChangeInfo)
        mCCN = self._resolveMailCCNAddreses(econtext, stateChangeInfo)
        
        options = {}
        if self.message_id_expression:
            options["Message-Id"] = self.message_id_expression(econtext)
        if self.in_replay_to_expression:
            options["In-Reply-To"] = self.in_replay_to_expression(econtext)
        
        self.mail_header_dtml.__dict__.update(econtext.__dict__)
        mHeader = self.mail_header_dtml(client=stateChangeInfo.object)
        
        #TODO fix this patch
        mHeader = unicode(mHeader,"latin-1").encode("latin-1","replace")
        mHeadCss = self.mail_head_css_dtml(client=stateChangeInfo.object)
        mBody = self.mail_body_dtml(client=stateChangeInfo.object)
        if mHeadCss:
            mBodyFull = "<html> " + mHeadCss + mBody + " </html>"
        else:
            mBodyFull = "<html> " + mBody + " </html>"
        try:
            if mTO or mCC or mCCN:
                log("mTo: " + str(mTO))
                log("mFROM: " + str(mFROM))
                log("mCC: " + str(mCC))
                log("mCCN: " + str(mCCN))
                log("mHeader: " + str(mHeader))
                log("mBody: " + str(mBody))
                #~ self.MailHost.secureSend(  mBodyFull, mTO,
                                                            #~ mFROM, mHeader,
                                                            #~ mCC, mCCN, "html",charset="utf-8", **options)
                lThread = SenderThread(self.MailHost, mTO, mFROM, mCC, mCCN, mHeader, mBodyFull, options)
                lThread.start()
                log("Sender Thread started succesfully by " + str(lThread))
        except:
            type, val, tb = sys.exc_info()
            traceback.print_exc(file=sys.stdout)
            warn("Mail cannot be sent : \nException type: %s \nException value: %s \nException tb: %s" % (type, val, tb) )
            return self.plone_utils.addPortalMessage( u"the notification mail can't be sent! the server network services are not correctly configured or a firewall is blocking the nameserver lookups \n error: %s " % type)
        
        
    def editMailerForm(self, mail_from_expression, mail_header_dtml, mail_head_css_dtml, mail_body_dtml,
                                            message_id_expression=None, in_replay_to_expression=None,
                                            mail_to_expression='', mail_to_list=[], mail_to_roles=[], mail_to_groups=[], 
                                            mail_cc_expression='', mail_cc_list=[], mail_cc_roles=[], mail_cc_groups=[], 
                                            mail_ccn_expression='', mail_ccn_list=[], mail_ccn_roles=[], mail_ccn_groups=[] ):
        #manage metadata for mail
        if in_replay_to_expression:
            self.in_replay_to_expression = Expression(in_replay_to_expression)
        if message_id_expression:
            self.message_id_expression = Expression(message_id_expression)
            
        #manage mail from
        if mail_from_expression:
            self.mail_from_expression = Expression(mail_from_expression)
        else:
            self.mail_from_expression=None
        
        #manage mail to
        if mail_to_expression:
            self.mail_to_expression = Expression(mail_to_expression)
        else:
            self.mail_to_expression=None
            
        self.mail_to_list = mail_to_list
        self.mail_to_roles = mail_to_roles
        self.mail_to_groups = mail_to_groups
        
        #manage mail cc
        if mail_cc_expression:
            self.mail_cc_expression = Expression( mail_cc_expression)
        else:
            self.mail_cc_expression=None
            
        self.mail_cc_list = mail_cc_list
        self.mail_cc_roles = mail_cc_roles
        self.mail_cc_groups = mail_cc_groups

        #manage mail cc
        if mail_ccn_expression:
            self.mail_ccn_expression = Expression( mail_ccn_expression)
        else:
            self.mail_ccn_expression=None
            
        self.mail_ccn_list = mail_ccn_list
        self.mail_ccn_roles = mail_ccn_roles
        self.mail_ccn_groups = mail_ccn_groups
        
        if mail_header_dtml:
            self.mail_header_dtml = DTMLMethod( mail_header_dtml)
        if mail_head_css_dtml:
            self.mail_head_css_dtml = DTMLMethod( mail_head_css_dtml )
        if mail_body_dtml:
            self.mail_body_dtml = DTMLMethod( mail_body_dtml )        
        
        # Clean all the attributes from [''] useless lists 
        for value in self.__dict__:
            if getattr(self,value) == ['']:
                setattr(self,value,[])
        
    def manage_editMailerFor(self, REQUEST=None):
        """ manage edit of this object """
        mail_from_expression = REQUEST.form['mail_from_expression']
        
        message_id_expression = REQUEST.form['message_id_expression']
        in_replay_to_expression = REQUEST.form['in_replay_to_expression']
        
        mail_to_expression = REQUEST.form['mail_to_expression']
        mail_to_list = REQUEST.form['mail_to_list'].split(',')
        mail_to_roles = REQUEST.form['mail_to_roles'].split(',')
        mail_to_groups = REQUEST.form['mail_to_groups'].split(',')
        
        mail_cc_expression = REQUEST.form['mail_cc_expression']
        mail_cc_list = REQUEST.form['mail_cc_list'].split(',')
        mail_cc_roles = REQUEST.form['mail_cc_roles'].split(',')
        mail_cc_groups = REQUEST.form['mail_cc_groups'].split(',')        
        
        mail_ccn_expression = REQUEST.form['mail_ccn_expression']
        mail_ccn_list = REQUEST.form['mail_ccn_list'].split(',')
        mail_ccn_roles = REQUEST.form['mail_ccn_roles'].split(',')
        mail_ccn_groups = REQUEST.form['mail_ccn_groups'].split(',')        

        mail_header_dtml = REQUEST.form['mail_header_dtml']
        mail_head_css_dtml = REQUEST.form['mail_head_css_dtml']   
        mail_body_dtml = REQUEST.form['mail_body_dtml']
                
        self.editMailerForm(mail_from_expression, mail_header_dtml, mail_head_css_dtml, mail_body_dtml,
                                            message_id_expression,in_replay_to_expression,
                                            mail_to_expression, mail_to_list, mail_to_roles, mail_to_groups, 
                                            mail_cc_expression, mail_cc_list, mail_cc_roles, mail_cc_groups, 
                                            mail_ccn_expression, mail_ccn_list, mail_ccn_roles, mail_ccn_groups )
        
        
        REQUEST.RESPONSE.redirect(self.absolute_url() + "/edit_mailer?manage_tabs_message=Mailer+correctly+changed")

    security.declarePublic('exprDocs')
    def exprDocs(self):
        """Returns documentation on guard expressions.
        """
        import os
        here = os.path.dirname(__file__)
        fn = os.path.join(here, 'doc', 'expressions.stx')
        f = open(fn, 'rt')
        try:
            text = f.read()
        finally:
            f.close()
        from DocumentTemplate.DT_Var import structured_text
        return structured_text(text)
