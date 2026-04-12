from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Cart(models.Model):
	class Status(models.TextChoices):
		ACTIVE = 'ACTIVE', 'Active'
		CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
		ABANDONED = 'ABANDONED', 'Abandoned'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
	products = models.ManyToManyField('inventory.Product', through='CartItem', related_name='carts')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-updated_at']
		constraints = [
			models.UniqueConstraint(
				fields=['user'],
				condition=models.Q(status='ACTIVE'),
				name='unique_active_cart_per_user',
			)
		]

	def __str__(self):
		return f"Cart<{self.user_id}>:{self.status}"


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='cart_items')
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-updated_at']
		constraints = [
			models.UniqueConstraint(fields=['cart', 'product'], name='unique_product_per_cart')
		]

	@property
	def subtotal(self):
		return self.unit_price_snapshot * self.quantity

	def __str__(self):
		return f"{self.cart_id} - {self.product.sku} x {self.quantity}"
