from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ('product_name_snapshot', 'product_sku_snapshot', 'quantity', 'unit_price', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
	list_filter = ('status',)
	search_fields = ('id', 'user__username', 'customer_email')
	inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('id', 'order', 'product_sku_snapshot', 'quantity', 'line_total')
	list_select_related = ('order', 'product')
