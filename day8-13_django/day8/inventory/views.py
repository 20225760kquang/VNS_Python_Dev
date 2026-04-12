from django.shortcuts import render
from .models import Product, StockTransaction, Category, Supplier
from django.db.models import Sum

def dashboard(request):
    # Advanced ORM Queries
    total_inventory_value = Product.objects.total_inventory_value()
    low_stock_products = Product.objects.low_stock().select_related('category', 'supplier')
    all_products_with_value = Product.objects.with_total_value().select_related('category', 'supplier')

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()

    # Recent transactions
    recent_transactions = StockTransaction.objects.select_related('product').order_by('-date')[:5]

    context = {
        'total_inventory_value': total_inventory_value,
        'low_stock_products': low_stock_products,
        'all_products': all_products_with_value,
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'inventory/dashboard.html', context)
