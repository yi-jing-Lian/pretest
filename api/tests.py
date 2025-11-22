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
        self.invalid_token = "invalid_token"

        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=50,
            quantity_in_stock=10
        )

        # 建立一個有效的促銷代碼
        self.promo = PromotionCode.objects.create(
            name="Black Friday Sale",
            code="BF2025",
            discount_type="percent",
            value=20,  # 20% off
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1)
        )
        self.promo.products.add(self.product)

    def test_missing_access_token(self):
        data = {
            'order_number': '12345',
            'products': [{"product_id": self.product.id, "quantity": 1}]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or missing access token", response.data['detail'])

    def test_invalid_access_token(self):
        data = {
            'access_token': self.invalid_token,
            'order_number': '12345',
            'products': [{"product_id": self.product.id, "quantity": 1}]
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
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "Order created successfully")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 8)

    def test_stock_updated_after_order(self):
        initial_stock = self.product.quantity_in_stock
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD999",
            "products": [
                {"product_id": self.product.id, "quantity": 3}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "Order created successfully")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock - 3)

    def test_successful_order_without_promo_code(self):
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD_NO_PROMO",
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['final_price'], 100)  # 50 * 2 

    def test_successful_order_with_valid_promo_code(self):
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD_WITH_PROMO",
            "promo_code": "BF2025",
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['final_price'], 80)  # 原價 100，折扣 20% → 80

    def test_order_with_invalid_promo_code(self):
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD_INVALID_PROMO",
            "promo_code": "WRONGCODE",
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Promo code not found", response.data['detail'])

    def test_order_with_expired_promo_code(self):
        expired_promo = PromotionCode.objects.create(
            name="Expired Sale",
            code="OLD2020",
            discount_type="fixed",
            value=10,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=5)
        )
        expired_promo.products.add(self.product)

        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD_EXPIRED_PROMO",
            "promo_code": "OLD2020",
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired promo code", response.data['detail'])

class RestockProductTestCase(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=50,
            quantity_in_stock=10
        )
        self.url = reverse('restock_product', args=[self.product.id])

    def test_restock_api(self):
        initial_stock = self.product.quantity_in_stock
        data = {"quantity": 10}

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("restocked", response.data['detail'])

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock + 10)


# class PromotionCodeTestCase(APITestCase):
#     def setUp(self):
#         self.product = Product.objects.create(
#             name="Test Product",
#             description="Test description",
#             price=100,
#             quantity_in_stock=50
#         )

#         self.promo = PromotionCode.objects.create(
#             name="Black Friday Sale",
#             code="BF2025",
#             discount_type="percent",
#             value=20,  # 20% off
#             start_date=timezone.now() - timedelta(days=1),
#             end_date=timezone.now() + timedelta(days=1)
#         )

#         self.promo.products.add(self.product)

#     def test_is_active(self):
#         self.assertTrue(self.promo.is_active())

#     def test_is_valid_with_correct_code(self):
#         self.assertTrue(self.promo.is_valid("BF2025"))

#     def test_is_valid_with_wrong_code(self):
#         self.assertFalse(self.promo.is_valid("WRONGCODE"))

#     def test_is_valid_with_expired_date(self):
#         self.promo.start_date = timezone.now() - timedelta(days=5)
#         self.promo.end_date = timezone.now() - timedelta(days=1)
#         self.promo.save()
#         self.assertFalse(self.promo.is_valid("BF2025"))

#     def test_apply_percent_discount(self):
#         original_price = 200
#         discounted_price = self.promo.apply_discount(original_price)
#         self.assertEqual(discounted_price, 160)

#     def test_apply_fixed_discount(self):
#         self.promo.discount_type = 'fixed'
#         self.promo.value = 30
#         self.promo.save()

#         original_price = 100
#         discounted_price = self.promo.apply_discount(original_price)
#         self.assertEqual(discounted_price, 70)

#     def test_discount_never_below_zero(self):
#         self.promo.discount_type = 'fixed'
#         self.promo.value = 150
#         self.promo.save()

#         original_price = 100
#         discounted_price = self.promo.apply_discount(original_price)
#         self.assertEqual(discounted_price, 0)
