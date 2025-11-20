from django.db import models
from django.utils import timezone
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name

    def adjust_stock(self, quantity):
        self.quantity_in_stock = max(0, self.quantity_in_stock - quantity)
        self.save()

    def restock(self, quantity):
        if quantity > 0:
            self.quantity_in_stock += quantity
            self.save()


class Order(models.Model):
    order_number = models.CharField(max_length=100, unique=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    products = models.ManyToManyField(Product, through='OrderProduct')

    def __str__(self):
        return self.order_number

    def update_stock(self):
        for order_product in self.orderproduct_set.all():
            order_product.product.adjust_stock(order_product.quantity)

    def calculate_total(self):
        subtotal = 0
        for order_product in self.orderproduct_set.all():
            subtotal += order_product.product.price * order_product.quantity

        for promo in Promotion.objects.filter(products__in=self.products.all()):
            if promo.is_active():
                subtotal = promo.apply_discount(subtotal)

        self.total_price = subtotal
        self.save()
        return subtotal


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    


class PromotionCode(models.Model):
    DISCOUNT_CHOICES = [
        ('percent', 'Percent'),
        ('fixed', 'Fixed'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    products = models.ManyToManyField('Product', related_name='promotions')

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def is_valid(self, input_code):
        now = timezone.now()
        return (
            self.start_date <= now <= self.end_date and
            self.code.lower() == input_code.lower()
        )

    def apply_discount(self, price):
        if self.discount_type == 'percent':
            return price * (1 - self.value / 100)
        elif self.discount_type == 'fixed':
            return max(0, price - self.value)
        return price

    def __str__(self):
        return f"{self.name} ({self.code})"