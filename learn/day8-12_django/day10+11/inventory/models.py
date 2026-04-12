from django.db import models
from django.db.models import F, Sum, ExpressionWrapper, DecimalField

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class ProductQuerySet(models.QuerySet):
    def low_stock(self):
        return self.filter(stock_quantity__lte=F('reorder_level'))

    def with_total_value(self):
        return self.annotate(
            total_value=ExpressionWrapper(
                F('stock_quantity') * F('unit_price'), 
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )

    def total_inventory_value(self):
        return self.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('stock_quantity') * F('unit_price'), 
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
        )['total'] or 0

class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def low_stock(self):
        return self.get_queryset().low_stock()

    def with_total_value(self):
        return self.get_queryset().with_total_value()

    def total_inventory_value(self):
        return self.get_queryset().total_inventory_value()

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)

    objects = ProductManager()

    @property
    def available_stock(self):
        return self.stock_quantity

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_product'
            )
        ]

    def __str__(self):
        return f"{self.product.sku} image"

class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Restock (IN)'),
        ('OUT', 'Sale/Usage (OUT)'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} - {self.quantity}"
