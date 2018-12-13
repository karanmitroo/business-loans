import json
from django.utils import timezone
from django.test import TestCase
from users.models import AnonData, CompanyData, UserData
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from users.test_json import TEST_JSON

class Eligibility_Test(TestCase):
    def setUp(self):
        self.url = reverse('user-eligibility')


    def response_to_json(self, response):
        json_response = json.loads(response.content.decode('utf-8').replace("'", '"'))
        return json_response

    def test_case_one(self):
        """
        Test Case 1
        """
        data = TEST_JSON["test_case_one"]
        response = self.client.post(self.url, data, format='json')
        req_response = self.response_to_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(req_response["status"], data["result"])


    def test_case_two(self):
        """
        Test Case 2
        """
        data = TEST_JSON["test_case_two"]
        response = self.client.post(self.url, data, format='json')
        req_response = self.response_to_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(req_response["status"], data["result"])


    def test_case_three(self):
        """
        Test Case 3
        """
        data = TEST_JSON["test_case_three"]
        response = self.client.post(self.url, data, format='json')
        req_response = self.response_to_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(req_response["status"], data["result"])


    def test_case_four(self):
        """
        Test Case 4
        """
        data = TEST_JSON["test_case_four"]
        response = self.client.post(self.url, data, format='json')
        req_response = self.response_to_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(req_response["status"], data["result"])
