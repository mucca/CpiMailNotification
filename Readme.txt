CpiMailNotification is a developing tool that allows developers to easily bound email and workflow transition.






Here follows an example of dic that builds an email:


{  'title' : "my_first_notification",
                                'selected_transition':"state1_to_state2",
                                'selected_workflow':"my_workflow",
                                'mail_from_expression':"string:xyz@cpiprogetti.it",
                                'mail_header_dtml':"<dtml-var Type> '<dtml-var Title>' some text",
                                'mail_body_dtml':
"""
some dtml text... <dtml-var Title> (<dtml-var Type>) some other text. <br> 
some text, some text, some text, some text... <br> 
""",
                                'mail_to_expression':"python:['mail1@cpiprogetti.it', 'mail2@cpiprogetti.it', 'mail3@cpiprogetti.it', ]" ,
                                'mail_to_list':[],
                                'mail_to_roles':[],
                                'mail_to_groups':[],
                                'mail_cc_expression':"",
                                'mail_cc_list':[],
                                'mail_cc_roles':[],
                                'mail_cc_groups':[],
                                'mail_ccn_expression':"",
                                'mail_ccn_list':[],
                                'mail_ccn_roles':[],
                                'mail_ccn_groups':[],    
}






Here follows how to bind the above dic/email with your instance of CpiMailNotification:


self.mailnotification_tool.addMailerFor( notifier['title'], 
					 notifier['selected_transition'], 
                                         notifier['selected_workflow'], 
                                         notifier['mail_from_expression'], 
                                         notifier['mail_header_dtml'], 
 					 notifier['mail_body_dtml'],
                                         mail_to_expression=notifier['mail_to_expression'], 
					 mail_to_list=notifier['mail_to_list'], 
					 mail_to_roles=notifier['mail_to_roles'], 
					 mail_to_groups=notifier['mail_to_groups'], 
                                         mail_cc_expression=notifier['mail_cc_expression'], 
					 mail_cc_list=notifier['mail_cc_list'], 						 					         mail_cc_roles=notifier['mail_cc_roles'], 
					 mail_cc_groups=notifier['mail_cc_groups'], 
                                         mail_ccn_expression=notifier['mail_ccn_expression'], 
					 mail_ccn_list=notifier['mail_ccn_list'], 						 						 mail_ccn_roles=notifier['mail_ccn_roles'], 
					 mail_ccn_groups=notifier['mail_ccn_groups'] )


Warning!!! Patch.py is a monkey patch for DCWorkflow.










