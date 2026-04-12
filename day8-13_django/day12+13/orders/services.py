from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from inventory.models import StockTransaction

from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user, shipping_address):
    try:
        cart = (
            Cart.objects.select_related("user")
            .prefetch_related("items__product")
            .get(user=user, status=Cart.Status.ACTIVE)
        )
    except Cart.DoesNotExist as exc:
        raise ValidationError({"detail": "Active cart not found."}) from exc

    cart_items = list(cart.items.all())
    if not cart_items:
        raise ValidationError({"detail": "Cart is empty."})

    total_amount = Decimal("0.00")
    order = Order.objects.create(
        user=user,
        cart=cart,
        customer_email=user.email,
        shipping_address=shipping_address,
        status=Order.Status.PENDING,
        total_amount=Decimal("0.00"),
    )

    order_items = []
    stock_transactions = []

    for cart_item in cart_items:
        product = cart_item.product
        updated = product.__class__.objects.filter(
            pk=product.pk,
            stock_quantity__gte=cart_item.quantity,
        ).update(stock_quantity=F("stock_quantity") - cart_item.quantity)

        if updated == 0:
            raise ValidationError({"detail": f"Insufficient stock for product {product.sku}."})

        line_total = cart_item.unit_price_snapshot * cart_item.quantity
        total_amount += line_total

        order_items.append(
            OrderItem(
                order=order,
                product=product,
                product_name_snapshot=product.name,
                product_sku_snapshot=product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price_snapshot,
                line_total=line_total,
            )
        )

        stock_transactions.append(
            StockTransaction(
                product=product,
                transaction_type="OUT",
                quantity=cart_item.quantity,
                notes=f"Order #{order.id} checkout",
            )
        )

    OrderItem.objects.bulk_create(order_items)
    StockTransaction.objects.bulk_create(stock_transactions)

    order.total_amount = total_amount
    order.save(update_fields=["total_amount"])

    cart.status = Cart.Status.CHECKED_OUT
    cart.save(update_fields=["status", "updated_at"])
    cart.items.all().delete()

    return order


@transaction.atomic
def cancel_order(order, actor, reason=""):
    if not actor.is_staff and order.user_id != actor.id:
        raise ValidationError({"detail": "You do not have permission to cancel this order."})

    non_cancelable = {Order.Status.SHIPPED, Order.Status.COMPLETED, Order.Status.CANCELLED}
    if order.status in non_cancelable:
        raise ValidationError({"detail": f"Order in status {order.status} cannot be cancelled."})

    order_items = list(order.items.select_related("product").all())
    stock_transactions = []

    note_suffix = f" - reason: {reason}" if reason else ""
    for item in order_items:
        if item.product_id is None:
            continue

        item.product.__class__.objects.filter(pk=item.product_id).update(
            stock_quantity=F("stock_quantity") + item.quantity
        )
        stock_transactions.append(
            StockTransaction(
                product_id=item.product_id,
                transaction_type="IN",
                quantity=item.quantity,
                notes=f"Order #{order.id} cancelled{note_suffix}",
            )
        )

    if stock_transactions:
        StockTransaction.objects.bulk_create(stock_transactions)

    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])

    return order
