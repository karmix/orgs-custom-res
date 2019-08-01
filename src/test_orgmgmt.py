# Copyright 2019, Doug Knight
# All Rights Reserved

import unittest
from unittest import mock
import orgmgmt
import requests
import json
import copy

mock_event_data = ()
mock_context_data = ()


class TestSend(unittest.TestCase):

    # Checking the serialized JSON data as a fixed string in
    # assert_called_once_with makes for fragile tests.  Instead, these
    # tests pass the extract_data_from_put method to mock as a side_effect
    # and use it to stash the json data when requests.put gets called.
    # Later, the assert_lambda_response method unpacks the json and
    # validates the resulting dict.

    def extract_data_from_put(self, *args, **kwargs):
        self.data_from_put = copy.deepcopy(kwargs['data'])

        if self.requests_put_response_exception:
            raise self.requests_put_response_exception

        response = requests.models.Response()
        response.url = args[0]
        response.status_code = self.requests_put_response_status_code
        response.reason = self.requests_put_response_reason
        return response


    def assert_lambda_response(self,
        data={},
        responseUrl='fake://response-url/'):

        self.requests_put_mock.assert_called_once_with(
            responseUrl,
            data=self.data_from_put,
            headers={
                'content-type': '',
                'content-length': str(len(self.data_from_put))
            }
        )

        data_from_json = json.loads(self.data_from_put)

        expected_data = self.expected_response.copy()
        expected_data.update(data)

        extra_keys = set(data_from_json.keys()) - set(expected_data.keys())
        assert not extra_keys, "unexpected response data: %s" % extra_keys

        missing_keys = set(expected_data.keys()) - set(data_from_json.keys())
        assert not missing_keys, "missing response data: %s" % missing_keys

        for key in data_from_json.keys():
            assert data_from_json[key] == expected_data[key], \
                   "unexpected value for response data '%s':\n" \
                   "expected : %s\n" \
                   "actual   : %s" % (key, expected_data[key],
                                      data_from_json[key])


    def setUp(self):
        self.event = {
            'ResponseURL': 'fake://response-url/',
            'StackId': 'STACK_ID',
            'RequestId': 'REQUEST_ID',
            'LogicalResourceId': 'LOGICAL_RESOURCE_ID'
        }

        self.context = mock.MagicMock()
        self.context.log_stream_name = 'LOG_STREAM_NAME'

        self.expected_response = {
            'RequestId': 'REQUEST_ID',
            'StackId': 'STACK_ID',
            'LogicalResourceId': 'LOGICAL_RESOURCE_ID',
            'PhysicalResourceId': 'LOG_STREAM_NAME',
            'Status': 'SUCCESS'
        }

        self.data_from_put = None

        self.requests_put_patch = mock.patch('requests.put')
        self.requests_put_mock = self.requests_put_patch.start()
        self.requests_put_mock.side_effect = self.extract_data_from_put

        self.requests_put_response_exception = None
        self.requests_put_response_status_code = 200
        self.requests_put_response_reason = 'OK'

        self.orgmgmt_print_patch = mock.patch('orgmgmt.print')
        self.orgmgmt_print_mock = self.orgmgmt_print_patch.start()
        

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
