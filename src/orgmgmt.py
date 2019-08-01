# Copyright 2019, Doug Knight
# All Rights Reserved

import json
import requests

FAILED = 'FAILED'
SUCCESS = 'SUCCESS'


def send(event,
         context,
         responseStatus,
         responseData=None,
         physicalResourceId=None,
         noEcho=None,
         reason=None,
         logger=None):

    class PrintLogger:
        def info(self, message):
            print(message)

    log = logger or PrintLogger()

    res = {}
    res['RequestId'] = event['RequestId']
    res['StackId'] = event['StackId']
    res['LogicalResourceId'] = event['LogicalResourceId']
    res['PhysicalResourceId'] = physicalResourceId or \
                                event.get('PhysicalResourceId') or \
                                context.log_stream_name
    res['Status'] = responseStatus

    if reason:
        res['Reason'] = reason
    elif responseStatus == FAILED:
        res['Reason'] = 'See the details in CloudWatch Log Stream: ' + \
                        context.log_stream_name

    if responseData is not None:
        res['Data'] = responseData

    if noEcho:
        res['NoEcho'] = noEcho

    put_data = json.dumps(res, separators=(',', ':'))

    log.info('submitting response data %s to url %s'
             % (put_data, event['ResponseURL']))

    try:
      response = requests.put(event['ResponseURL'],
                              data=put_data,
                              headers={
                                'content-type': '',
                                'content-length': str(len(put_data))
                              })
      response.raise_for_status()
    except Exception as e:
      log.info('call to requests.put failed: ' + str(e))
