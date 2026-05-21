from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.clients.models import Client
from apps.locations.models import Destination, Warehouse
from django.core.exceptions import ValidationError

class ClientModelTest(TestCase):
    def test_auto_generate_client_code(self):
        client = Client.objects.create(full_name="Ivan Ivanov")
        self.assertTrue(client.client_code.startswith("CL"))

    def test_manual_client_code(self):
        client = Client.objects.create(full_name="Petr Petrov", client_code="MYCODE123")
        self.assertEqual(client.client_code, "MYCODE123")
        
    def test_normalize_client_code(self):
        client = Client.objects.create(full_name="Anna", client_code="  customCode  ")
        # should trim and uppercase
        self.assertEqual(client.client_code, "CUSTOMCODE")

    def test_duplicate_client_code(self):
        Client.objects.create(full_name="First", client_code="DUP123")
        client2 = Client(full_name="Second", client_code="dup123") # will be uppercase
        with self.assertRaises(ValidationError) as context:
            client2.clean()
        self.assertIn("client_code", context.exception.message_dict)

class ClientItemAPITest(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        # Create a user and authenticate if needed, assuming open or we need to login
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client_api.force_authenticate(user=self.user)
        
        self.client_obj = Client.objects.create(full_name="Test Client", client_code="API123")
        self.destination = Destination.objects.create(name="Moscow", code="MOW")
        self.warehouse = Warehouse.objects.create(name="Main WH", code="WH1")
        
        self.item_data = {
            "destination": self.destination.id,
            "warehouse": self.warehouse.id,
            "weight_kg": 10.5,
            "volume_m3": 0.1,
            "client_code": "API123"
        }

    def test_create_item_with_client_code(self):
        response = self.client_api.post('/api/v1/items/', self.item_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['client'], self.client_obj.id)

    def test_create_item_with_invalid_client_code(self):
        data = self.item_data.copy()
        data['client_code'] = "INVALID"
        response = self.client_api.post('/api/v1/items/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('client_code', response.data)

    def test_create_item_with_both_client_and_client_code(self):
        data = self.item_data.copy()
        data['client'] = self.client_obj.id
        response = self.client_api.post('/api/v1/items/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
