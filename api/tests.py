from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Product, Order, OrderProduct, Promotion
from django.utils import timezone
from datetime import timedelta

class OrderTestCase(APITestCase):
    # 定義可接受的 token
    ACCEPTED_TOKEN = 'omni_pretest_token'

    def setUp(self):
        """
        在每個測試前會被執行，這裡可以設置測試所需的初始資料
        """
        self.url = reverse('import_order')  # 假設你的 URL 名稱是 import_order
        self.valid_data = {
            "order_number": "ORD12345",
            "total_price": 99.99
        }
        self.invalid_data = {
            "order_number": "ORD12345"
        }
        self.invalid_token = "invalid_token"

        # 建立一個測試用商品
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=50,
            quantity_in_stock=10
        )

    def test_missing_access_token(self):
        """測試當缺少有效的 token 時，應返回 400 Bad Request"""
        data = {
            'order_number': '12345',
            'total_price': 100
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or missing access token", response.data['detail'])

    def test_invalid_access_token(self):
        """測試當使用無效的 token 時，應返回 400 Bad Request"""
        data = {
            'access_token': self.invalid_token,
            'order_number': '12345',
            'total_price': 100
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or missing access token", response.data['detail'])

    def test_missing_required_fields(self):
        """測試當請求中缺少 required fields 時，應返回 400 Bad Request"""
        data = {
            'access_token': self.ACCEPTED_TOKEN,
            'order_number': '12345'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data['detail'])

    def test_successful_order_creation(self):
        """測試成功建立訂單"""
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "ORD123",
            "total_price": 150.00,
            "products": [
                {"product_id": self.product.id, "quantity": 2}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        print(response.data)  # Debug 用

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "Order created successfully")

        # 確認庫存有扣減
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 8)

    def test_invalid_data(self):
        """
        測試無效數據（如缺少 total_price）時應返回 400 Bad Request
        """
        data = {
            "access_token": self.ACCEPTED_TOKEN,
            "order_number": "12345"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data['detail'])
    def test_stock_updated_after_order(self):
        """測試建立訂單後，商品庫存是否正確扣減"""
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

        # 重新讀取商品庫存
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock - 3)

    def test_restock_api(self):
        initial_stock = self.product.quantity_in_stock

        url = reverse('restock_product', args=[self.product.id])
        data = {"quantity": 10}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("restocked", response.data['detail'])

        # 確認庫存增加
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, initial_stock + 10)

class PromotionTestCase(APITestCase):
    def setUp(self):
        # 建立商品
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=100,
            quantity_in_stock=50
        )

        # 建立訂單
        self.order = Order.objects.create(
            order_number="PROMO123",
            total_price=0
        )

        # 訂單商品 (買 2 個)
        OrderProduct.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )

        # 建立促銷活動 (打 8 折)
        self.promo = Promotion.objects.create(
            name="Black Friday Sale",
            discount_type="percent",
            value=20,  # 20% off
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1)
        )
        self.promo.products.add(self.product)

    def test_promotion_applied_to_order(self):
        """測試促銷活動是否正確套用到訂單總價"""
        final_price = self.order.calculate_total()

        # 原始總價 = 100 * 2 = 200
        # 套用 20% 折扣後 = 160
        self.assertEqual(final_price, 160)
        self.assertEqual(self.order.total_price, 160)
