from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Order, Product, OrderProduct
from .decorators import validate_access_token

@api_view(['POST'])
@validate_access_token
def import_order(request):
    order_number = request.data.get('order_number')
    total_price = request.data.get('total_price')
    products_data = request.data.get('products', [])

    if not order_number or not total_price:
        return Response(
            {"detail": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 建立訂單
    order = Order.objects.create(
        order_number=order_number,
        total_price=total_price
    )

    # 建立 OrderProduct 關聯
    for item in products_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": f"Product with id {product_id} not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        OrderProduct.objects.create(
            order=order,
            product=product,
            quantity=quantity
        )

    # 更新庫存
    order.update_stock()

    return Response(
        {"detail": "Order created successfully"},
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
def restock_product(request, product_id):
    quantity = request.data.get('quantity', 0)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    if quantity <= 0:
        return Response({"detail": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

    product.restock(quantity)
    return Response({"detail": f"{product.name} restocked by {quantity}"}, status=status.HTTP_200_OK)
