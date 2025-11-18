from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_number', 'total_price', 'created_time']
        read_only_fields = ['created_time']
