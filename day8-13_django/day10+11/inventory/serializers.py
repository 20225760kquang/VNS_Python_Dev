from rest_framework import serializers
from .models import Category, Supplier, Product, ProductImage, StockTransaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    # Dùng SerializerMethodField hoặc trực tiếp truy xuất các biến của QuerySet annotate
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='supplier', write_only=True
    )

    is_low_stock = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'unit_price', 'stock_quantity', 'reorder_level',
            'category', 'category_id', 'supplier', 'supplier_id',
            'total_value', 'is_low_stock', 'images'
        ]

    def get_is_low_stock(self, obj):
        return obj.stock_quantity <= obj.reorder_level

class StockTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = StockTransaction
        fields = ['id', 'product', 'product_name', 'transaction_type', 'quantity', 'date', 'notes']
