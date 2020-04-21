from celery_tasks.main import celery_app
# import sys
# sys.path.insert(0, '../../../')
from celery_tasks.sms.yuntongxun.ccp_sms import CCP

@celery_app.task(name='ccp_send_sms_code')
def ccp_send_sms_code(mobile, sms_code):
    result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    return result