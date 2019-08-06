import unittest
import os
import json
import time

from google.cloud import pubsub_v1, datastore
import requests
import backoff

from integration import setup_test
from integration import mock_server

setup_test.setup_test()


class TestSlackBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._client = datastore.Client(_http=requests.Session, project=os.environ.get("PROJECT_ID"))
        # cls.publisher = pubsub_v1.PublisherClient()
        # Use PubSub emulator topic defined in app
        # cls.publisher_topic_name = 'projects/{project_id}/topics/{topic}'.format(
        # project_id=os.environ.get("PROJECT_ID"),
        # topic='file-upload')
        cls.slack_api_url = os.getenv("SLACK_API_URL")
        cls.salesforce_api_url = os.getenv("SF_API_URL")
        cls.app_url = "http://localhost:8000"
        cls.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        cls.response = json.dumps({
            "ok": True,
        })
        cls.message_id = cls.setup_ticket_test_gcp_support()

    def tearDown(self):
        mock_server.reset_mock_server_response(self.slack_api_url, "/(.*)")

    def get_entity(self, client, kind, id):
        """Get a specific message from Datastore by id"""
        key = client.key('message', id)
        entity = client.get(key)
        return entity

    @backoff.on_exception(backoff.constant, AssertionError, jitter=None, interval=1, max_tries=20)
    def slack_client_called(self, at_least: int, at_most: int, body: dict):
        verify = mock_server.verify_min_max(self.slack_api_url, "/(.*)", at_least, at_most, body)
        if verify == 202:
            return True
        else:
            raise AssertionError("Could not assert that slack-client was called "
                                 "at least {} and at most {} times".format(at_least, at_most))

    @backoff.on_exception(backoff.constant, AssertionError, jitter=None, interval=1, max_tries=20)
    def assert_datastore_updated(self, message_id, key, exp_value):
        entity = self.get_entity(self._client, "message", self.message_id)
        if entity.get(key) == exp_value:
            return True
        else:
            raise AssertionError("Could not assert that datastore has been updated. Retrying...")

    @classmethod
    def setup_ticket_test_gcp_support(cls):
        mock_server.add_mock_response_with_json(cls.slack_api_url, "/(.*)", 200, cls.response)

        body = {
            "text": "Test request",
            "team_domain": "test-team-domain",
            "user_name": "mock-user",
            "channel_name": "mock-channel"
        }
        url = "{}/slack/gcp_support".format(cls.app_url)
        req = requests.post(url, data=body, headers=cls.headers)
        message_id = req.text.split("*")[1]
        time.sleep(5)  # Artifical sleep for thread to finish processing
        mock_server.reset_mock_server_response(cls.slack_api_url, "/(.*)")
        return message_id

    def test_status(self):
        body = {
            "text": self.message_id,
            "team_domain": "test-team-domain",
            "user_name": "mock-user",
            "channel_name": "mock-channel"
        }
        url = "{}/status".format(self.app_url)
        req = requests.post(url, data=body, headers=self.headers)
        self.assertTrue(req.status_code == 200)
        status = req.text.split("*")[3]
        self.assertEqual("Completed", status)

    def test_response(self):
        mock_server.add_mock_response_with_json(self.slack_api_url, "/(.*)", 200, self.response)
        body = {
            "text": self.message_id,
            "team_domain": "test team domain",
            "user_name": "mock user",
            "channel_name": "mock channel"
        }
        url = "{}/response".format(self.app_url)
        req = requests.post(url, data=body, headers=self.headers)
        self.assertTrue(req.status_code == 200)

    def test_resolve_message(self):
        mock_server.add_mock_response_with_json(self.slack_api_url, "/(.*)", 200, self.response)
        body = {
            "text": self.message_id,
            "team_domain": "test team domain",
            "user_name": "mock user",
            "channel_name": "mock channel"
        }
        url = "{}/resolve_message".format(self.app_url)
        req = requests.post(url, data=body, headers=self.headers)
        self.assertTrue(req.status_code == 200)
        # Assert datastore updated
        self.assert_datastore_updated(message_id=self.message_id, key="status", exp_value="Completed")
        self.assertTrue(self.slack_client_called(at_least=1, at_most=1, body=None))
