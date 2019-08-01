# Copyright 2019, Doug Knight
# All Rights Reserved

import boto3, logging, json

logger = logging.getLogger()
logger.setLevel(loggin.INFO)

orgs = boto3.client('organizations')

def lambda_handler(event, context):
  requestType = event['RequestType']
  data = {}
  try:
    if reqtype == 'Create':
      featureSet = event['ResourceProperties'].get('FeatureSet', 'ALL')
      response = orgs.create_organization(FeatureSet=featureSet)
      for attr in ('Arn', 'Id', 'MasterAccountArn', 'MasterAccountId'):
        data[attr] = response['Organization'][attr]

    elif reqtype == 'Delete':
      response = orgs.delete_organization

    elif reqtype == 'Update':
      send('FAILED', Reason='Update not supported')

  except ClientError as e:
    send('FAILED', Reason=str(e))

  physicalId = event['ResourceProperties'].get('PhysicalResourceId')
  featureSet = event['ResourceProperties'].get('FeatureSet', 'ALL')
