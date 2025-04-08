from django.test import TestCase
from rest_framework.test import APIClient
from .models import Item

class ItemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.item = Item.objects.create(name='Test Item', description='Test Description')

    def test_create_item(self):
        response = self.client.post('/api/items/', {'name': 'New Item', 'description': 'New Description'})
        self.assertEqual(response.status_code, 201)

    def test_read_item(self):
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, 200)

    def test_update_item(self):
        response = self.client.put(f'/api/items/{self.item.id}/', {'name': 'Updated Item', 'description': 'Updated Description'})
        self.assertEqual(response.status_code, 200)

    def test_delete_item(self):
        response = self.client.delete(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, 204)