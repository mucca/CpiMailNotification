from  AccessControl import ModuleSecurityInfo
import logging

security = ModuleSecurityInfo('Products.CpiMailNotification.debug')

logger = logging.getLogger('CpiMailNotification')

security.declarePublic('log')
log = logger.info
security.declarePublic('warn')
warn = logger.warn