from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Product, Order, OrderProduct, PromotionCode
from django.utils import timezone
from datetime import timedelta

class OrderTestCase(APITestCase):
    ACCEPTED_TOKEN = 'omni_pretest_token'

    def setUp(self):
        self.url = reverse('import_order')
        self.valid_data = {
            "order_number": "ORD12345",
            "total_price": 99.99
        }
        self.invalid_data = {
            "order_number": "ORD12345"
        }
        self.invalid_token = "invalid_token"

        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=50,
            quantity_in_stock=10
        )

    def test_missing_access_token(self):
        data = {
            'order_number': '12345',
            'total_price': 100
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or missing access token", response.data['detail'])

    def test_invalid_access_token(self):
        data = {
            'access_token': self.invalid_token,
            'order_number': '12345',
            'total_price': 100
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or missing access token", response.data['detail'])

    def test_missing_required_fields(self):
        data = {
            'access_token': self.ACCEPTED_TOKEN,
            'order_number': '12345'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data['detail'])

    def test_successful_order_creation(self):
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD123",
            "total_price": 150.00,
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        print(response.data) 

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "Order created successfully")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 8)

    def test_invalid_data(self):
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "12345"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data['detail'])
    def test_stock_updated_after_order(self):
        initial_stock = self.product.quantity_in_stock

        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD999",
            "total_price": 100.00,
            "products": [
                {"product_id": self.product.id, "quantity": 3}
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "Order created successfully")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock - 3)

    def test_restock_api(self):
        initial_stock = self.product.quantity_in_stock

        url = reverse('restock_product', args=[self.product.id])
        data = {"quantity": 10}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("restocked", response.data['detail'])

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock + 10)

# TODO: update order model and api to apply promote code
class PromotionCodeTestCase(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=100,
            quantity_in_stock=50
        )

        self.promo = PromotionCode.objects.create(
            name="Black Friday Sale",
            code="BF2025",
            discount_type="percent",
            value=20,  # 20% off
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1)
        )

        self.promo.products.add(self.product)

    def test_is_active(self):
        self.assertTrue(self.promo.is_active())

    def test_is_valid_with_correct_code(self):
        self.assertTrue(self.promo.is_valid("BF2025"))

    def test_is_valid_with_wrong_code(self):
        self.assertFalse(self.promo.is_valid("WRONGCODE"))

    def test_is_valid_with_expired_date(self):
        self.promo.start_date = timezone.now() - timedelta(days=5)
        self.promo.end_date = timezone.now() - timedelta(days=1)
        self.promo.save()
        self.assertFalse(self.promo.is_valid("BF2025"))

    def test_apply_percent_discount(self):
        original_price = 200
        discounted_price = self.promo.apply_discount(original_price)
        self.assertEqual(discounted_price, 160)

    def test_apply_fixed_discount(self):
        self.promo.discount_type = 'fixed'
        self.promo.value = 30
        self.promo.save()

        original_price = 100
        discounted_price = self.promo.apply_discount(original_price)
        self.assertEqual(discounted_price, 70)

    def test_discount_never_below_zero(self):
        self.promo.discount_type = 'fixed'
        self.promo.value = 150
        self.promo.save()

        original_price = 100
        discounted_price = self.promo.apply_discount(original_price)
        self.assertEqual(discounted_price, 0)
