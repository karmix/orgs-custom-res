# Copyright 2019, Doug Knight
# All Rights Reserved

import unittest
from unittest import mock
import organization
from copy import deepcopy


class TestOrganization(unittest.TestCase):

    # Checking the serialized JSON data as a fixed string in
    # assert_called_once_with makes for fragile tests.  Instead, these
    # tests pass the extract_data_from_put method to mock as a side_effect
    # and use it to stash the json data when requests.put gets called.
    # Later, the assert_lambda_response method unpacks the json and
    # validates the resulting dict.

    def setUp(self):
        self.event = {
            'ResponseURL': 'fake://response-url/',
            'StackId': 'STACK_ID',
            'RequestId': 'REQUEST_ID',
            'LogicalResourceId': 'LOGICAL_RESOURCE_ID'

            'RequestType': 'Create',
            'ResourceProperties': {}
        }

        self.context = mock.MagicMock()
        self.context.log_stream_name = 'LOG_STREAM_NAME'

# # ACCESS_DENIED:
# "
# botocore.errorfactory.AccessDeniedException: An error occurred (AccessDeniedException) when calling the CreateOrganization operation: You don't have permissions to access this resource.
# "
# 
# # SUCCESS:
# "
# {'Organization': {'Id': 'o-4snun182qf', 'Arn': 'arn:aws:organizations::111111111111:organization/o-4snun182qf', 'FeatureSet': 'ALL', 'MasterAccountArn': 'arn:aws:organizations::111111111111:account/o-4snun182qf/111111111111', 'MasterAccountId': '111111111111', 'MasterAccountEmail': 'orgs-test@example.com', 'AvailablePolicyTypes': [{'Type': 'SERVICE_CONTROL_POLICY', 'Status': 'ENABLED'}]}, 'ResponseMetadata': {'RequestId': '9c268113-edb3-40e9-8c7a-f9c71c13f21b', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '9c268113-edb3-40e9-8c7a-f9c71c13f21b', 'content-type': 'application/x-amz-json-1.1', 'content-length': '385', 'date': 'Wed, 31 Jul 2019 08:04:28 GMT'}, 'RetryAttempts': 0}}
# "
# 
# # ALREADY_CREATED
# "botocore.errorfactory.AlreadyInOrganizationException: An error occurred (AlreadyInOrganizationException) when calling the CreateOrganization operation: The AWS account is already a member of an organization.
# "
# 
# # SUCCESSFUL REMOVE:
# "
# {'ResponseMetadata': {'RequestId': '7276a45b-3396-4e4a-8013-7f3ec1a9c2de', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '7276a45b-3396-4e4a-8013-7f3ec1a9c2de', 'content-type': 'application/x-amz-json-1.1', 'content-length': '0', 'date': 'Wed, 31 Jul 2019 08:06:21 GMT'}, 'RetryAttempts': 0}}
# "
# 
# # ALREADY_REMOVED:
# "
# botocore.errorfactory.AWSOrganizationsNotInUseException: An error occurred (AWSOrganizationsNotInUseException) when calling the DeleteOrganization operation: Your account is not a member of an organization.
# "

        self.create_organization_result = {
            'Organization': {
                'Id': 'ORG_ID'
                'Arn': 'ORG_ARN',
                'FeatureSet': 'ALL',
                'MasterAccountArn': 'MASTER_ACCOUNT_ARN',
                'MasterAccountId': 'MASTER_ACCOUNT_ID',
                'MasterAccountEmail': 'MASTER_ACCOUNT_EMAIL',
                'AvailablePolicyTypes': [{
                    'Type': 'SERVICE_CONTROL_POLICY',
                    'Status': 'ENABLED'
                }]
            },
            'ResponseMetadata': { 'Test': 'Metadata' }
        }


        self.delete_organization_result = None
botocore.errorfactory.AWSOrganizationsNotInUseException

        self.boto3_client_patch = mock.patch('boto3.client')
        self.boto3_client_mock = self.boto3_client_patch.start()

        self.boto3_client_mock.create_organization.return_value = \
            self.create_organization_result

        self.boto3_client_mock.delete_organization.return_value = \
            self.delete_organization_result

        self.orgmgmt_send_patch = mock.patch('organization.send')
        self.orgmgmt_send_mock = self.orgmgmt_send_patch.start()

        self.expected_send_kwargs_data = {
            'Arn': 'ORG_ARN',
            'Id': 'ORG_ID',
            'MasterAccountArn': 'MASTER_ACCOUNT_ARN',
            'MasterAccountId': 'MASTER_ACCOUNT_ID'
        }
        self.expected_send_args = [deepcopy(event), context, 'SUCCESS']
        self.expected_send_kwargs = {
            'physicalResourceId': 'ORG_ID',
            'responseData':  {
                'Arn': 'ORG_ARN',
                'Id': 'ORG_ID',
                'MasterAccountArn': 'MASTER_ACCOUNT_ARN',
                'MasterAccountId': 'MASTER_ACCOUNT_ID'
            }
            'logger': self.mock_logger
        }



    def tearDown(self):
        self.orgmgmt_print_patch.stop()
        self.requests_put_patch.stop()


    def test_response_for_success(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.assert_lambda_response()


    def test_response_for_failed_without_reason(self):
        orgmgmt.send(self.event, self.context, orgmgmt.FAILED)

        self.expected_response['Status'] = 'FAILED'
        self.expected_response['Reason'] = \
            'See the details in CloudWatch Log Stream: LOG_STREAM_NAME'
        self.assert_lambda_response()


    def test_response_for_failed_with_reason(self):
        orgmgmt.send(self.event, self.context, orgmgmt.FAILED,
                     reason='I said so.')

        self.expected_response['Status'] = 'FAILED'
        self.expected_response['Reason'] = 'I said so.'
        self.assert_lambda_response()


    def test_response_for_success_with_reason(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS,
                     reason='I said so.')

        self.expected_response['Reason'] = 'I said so.'
        self.assert_lambda_response()


    def test_response_with_data(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS,
                     responseData={})

        self.expected_response['Data'] = {}
        self.assert_lambda_response()


    def test_response_with_special_characters(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS,
                     reason="escape special characters: \\, \", \n, & \r")

        self.expected_response['Reason'] = \
            "escape special characters: \\, \", \n, & \r"
        self.assert_lambda_response()


    def test_response_with_new_response_url_in_event(self):
        self.event['ResponseURL'] = 'fake://another-response-url/'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.assert_lambda_response(
            responseUrl='fake://another-response-url/'
        )


    def test_response_with_new_request_id_in_event(self):
        self.event['RequestId'] = 'ANOTHER_REQUEST_ID'
        self.expected_response['RequestId'] = 'ANOTHER_REQUEST_ID'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.assert_lambda_response()


    def test_response_with_new_stack_id_in_event(self):
        self.event['StackId'] = 'ANOTHER_STACK_ID'
        self.expected_response['StackId'] = 'ANOTHER_STACK_ID'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.assert_lambda_response()


    def test_response_with_new_logical_resource_id_in_event(self):
        self.event['LogicalResourceId'] = 'ANOTHER_LOGICAL_RESOURCE_ID'
        self.expected_response['LogicalResourceId'] = \
            'ANOTHER_LOGICAL_RESOURCE_ID'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.assert_lambda_response()


    def test_response_for_failed_with_new_log_stream_name_in_event(self):
        self.context.log_stream_name = 'ANOTHER_LOG_STREAM_NAME'

        orgmgmt.send(self.event, self.context, orgmgmt.FAILED)

        self.expected_response['Status'] = 'FAILED'
        self.expected_response['PhysicalResourceId'] = \
            'ANOTHER_LOG_STREAM_NAME'
        self.expected_response['Reason'] = \
            'See the details in CloudWatch Log Stream: ANOTHER_LOG_STREAM_NAME'
        self.assert_lambda_response()


    def test_response_with_physical_id_in_event(self):
        self.event['PhysicalResourceId'] = 'PHYSICAL_RESOURCE_ID'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        self.expected_response['PhysicalResourceId'] = 'PHYSICAL_RESOURCE_ID'
        self.assert_lambda_response()


    def test_response_with_physical_id_in_args(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS,
                     physicalResourceId='TEST_ID')

        self.expected_response['PhysicalResourceId'] = 'TEST_ID'
        self.assert_lambda_response()


    def test_response_with_physical_id_in_args_and_event(self):
        self.event['PhysicalResourceId'] = 'PHYSICAL_RESOURCE_ID'

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS,
                     physicalResourceId='TEST_ID')

        self.expected_response['PhysicalResourceId'] = 'TEST_ID'
        self.assert_lambda_response()


    def test_response_with_noecho_in_args(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS, noEcho=True)

        self.expected_response['NoEcho'] = True
        self.assert_lambda_response()


    def test_logs_for_success_without_logger(self):
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        # extract message from first argument in each call to print
        messages = [x[0][0] for x in self.orgmgmt_print_mock.call_args_list]
        self.assertEqual(
            messages,
            ['submitting response data ' + self.data_from_put +
             ' to url fake://response-url/']
        )


    def test_logs_for_exception_from_put_without_logger(self):
        self.requests_put_response_exception = Exception('exception from put')

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        messages = [x[0][0] for x in self.orgmgmt_print_mock.call_args_list]
        self.assertEqual(
            messages, [
                'submitting response data ' + self.data_from_put +
                ' to url fake://response-url/',

                'call to requests.put failed: exception from put'
            ]
        )


    def test_logs_for_exception_from_put_with_logger(self):
        self.requests_put_response_exception = Exception('exception from put')
        logger = mock.MagicMock()

        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS, logger=logger)

        messages = [x[0][0] for x in logger.info.call_args_list]
        self.assertEqual(
            messages, [
                'submitting response data ' + self.data_from_put +
                ' to url fake://response-url/',

                'call to requests.put failed: exception from put'
            ]
        )


    def test_logs_for_error_from_put_without_logger(self):
        self.requests_put_response_status_code = 500
        self.requests_put_response_reason = 'Internal Server Error'
        
        orgmgmt.send(self.event, self.context, orgmgmt.SUCCESS)

        # extract message from first argument in each call to print
        messages = [x[0][0] for x in self.orgmgmt_print_mock.call_args_list]
        self.assertEqual(
            messages, [
                'submitting response data ' + self.data_from_put +
                ' to url fake://response-url/',

                'call to requests.put failed: 500 Server Error: Internal '
                'Server Error for url: fake://response-url/'
            ]
        )
