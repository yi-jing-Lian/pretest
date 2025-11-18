from django.urls import path
from api.views import import_order, restock_product

urlpatterns = [
    path('import-order/', import_order, name='import_order'),
    path('products/<int:product_id>/restock/', restock_product, name='restock_product'),
]
