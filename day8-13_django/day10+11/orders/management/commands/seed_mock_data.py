from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from cart.models import Cart, CartItem
from inventory.models import Category, Product, StockTransaction, Supplier
from orders.models import Order, OrderItem
from orders.signals import enqueue_order_confirmation_email


class Command(BaseCommand):
    help = 'Seed mock data for inventory, cart, and orders.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing cart/order/inventory transactional data before seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self._reset_data()

        users = self._seed_users()
        categories = self._seed_categories()
        suppliers = self._seed_suppliers()
        products = self._seed_products(categories, suppliers)

        self._seed_active_cart(users['alice'], products)
        self._seed_orders_without_signal(users['bob'], products)

        self.stdout.write(self.style.SUCCESS('Seeded mock data successfully.'))

    def _reset_data(self):
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        StockTransaction.objects.all().delete()
        Product.objects.all().delete()
        Supplier.objects.all().delete()
        Category.objects.all().delete()

    def _seed_users(self):
        User = get_user_model()

        admin, _ = User.objects.get_or_create(
            username='admin_seed',
            defaults={
                'email': 'admin_seed@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin.set_password('Admin@123')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=['password', 'is_staff', 'is_superuser'])

        alice, _ = User.objects.get_or_create(
            username='alice',
            defaults={'email': 'alice@example.com', 'is_staff': False, 'is_superuser': False},
        )
        alice.set_password('Alice@123')
        alice.save(update_fields=['password'])

        bob, _ = User.objects.get_or_create(
            username='bob',
            defaults={'email': 'bob@example.com', 'is_staff': False, 'is_superuser': False},
        )
        bob.set_password('Bob@12345')
        bob.save(update_fields=['password'])

        return {'admin': admin, 'alice': alice, 'bob': bob}

    def _seed_categories(self):
        electronics, _ = Category.objects.get_or_create(
            name='Electronics',
            defaults={'description': 'Electronic devices and accessories'},
        )
        office, _ = Category.objects.get_or_create(
            name='Office Supplies',
            defaults={'description': 'Office and productivity products'},
        )
        return {'electronics': electronics, 'office': office}

    def _seed_suppliers(self):
        techcorp, _ = Supplier.objects.get_or_create(
            name='TechCorp',
            defaults={
                'contact_email': 'sales@techcorp.com',
                'phone': '0900000001',
                'address': 'Hanoi, Vietnam',
            },
        )
        officehub, _ = Supplier.objects.get_or_create(
            name='OfficeHub',
            defaults={
                'contact_email': 'support@officehub.com',
                'phone': '0900000002',
                'address': 'Ho Chi Minh City, Vietnam',
            },
        )
        return {'techcorp': techcorp, 'officehub': officehub}

    def _seed_products(self, categories, suppliers):
        product_specs = [
            {
                'sku': 'LAP-001',
                'name': 'Laptop Pro 14',
                'category': categories['electronics'],
                'supplier': suppliers['techcorp'],
                'unit_price': Decimal('1200.00'),
                'stock_quantity': 45,
                'reorder_level': 8,
            },
            {
                'sku': 'MOU-001',
                'name': 'Wireless Mouse',
                'category': categories['electronics'],
                'supplier': suppliers['techcorp'],
                'unit_price': Decimal('25.50'),
                'stock_quantity': 120,
                'reorder_level': 20,
            },
            {
                'sku': 'KEY-001',
                'name': 'Mechanical Keyboard',
                'category': categories['electronics'],
                'supplier': suppliers['techcorp'],
                'unit_price': Decimal('85.00'),
                'stock_quantity': 65,
                'reorder_level': 15,
            },
            {
                'sku': 'NTE-001',
                'name': 'Notebook A5',
                'category': categories['office'],
                'supplier': suppliers['officehub'],
                'unit_price': Decimal('3.20'),
                'stock_quantity': 350,
                'reorder_level': 60,
            },
        ]

        products = {}
        for spec in product_specs:
            product, _ = Product.objects.update_or_create(
                sku=spec['sku'],
                defaults={
                    'name': spec['name'],
                    'category': spec['category'],
                    'supplier': spec['supplier'],
                    'unit_price': spec['unit_price'],
                    'stock_quantity': spec['stock_quantity'],
                    'reorder_level': spec['reorder_level'],
                },
            )
            products[spec['sku']] = product

        return products

    def _seed_active_cart(self, user, products):
        Cart.objects.filter(user=user).exclude(status=Cart.Status.ACTIVE).delete()
        cart, _ = Cart.objects.get_or_create(user=user, status=Cart.Status.ACTIVE)
        cart.items.all().delete()

        CartItem.objects.create(
            cart=cart,
            product=products['MOU-001'],
            quantity=2,
            unit_price_snapshot=products['MOU-001'].unit_price,
        )
        CartItem.objects.create(
            cart=cart,
            product=products['NTE-001'],
            quantity=5,
            unit_price_snapshot=products['NTE-001'].unit_price,
        )

    def _seed_orders_without_signal(self, user, products):
        post_save.disconnect(enqueue_order_confirmation_email, sender=Order)
        try:
            order = Order.objects.create(
                user=user,
                customer_email=user.email,
                shipping_address='123 Seed Street, Hanoi',
                status=Order.Status.PROCESSING,
                total_amount=Decimal('0.00'),
            )

            items = [
                {'product': products['LAP-001'], 'quantity': 1},
                {'product': products['KEY-001'], 'quantity': 2},
            ]

            total = Decimal('0.00')
            for item in items:
                product = item['product']
                qty = item['quantity']
                line_total = product.unit_price * qty
                total += line_total

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name_snapshot=product.name,
                    product_sku_snapshot=product.sku,
                    quantity=qty,
                    unit_price=product.unit_price,
                    line_total=line_total,
                )

                Product.objects.filter(pk=product.pk).update(stock_quantity=product.stock_quantity - qty)
                StockTransaction.objects.create(
                    product=product,
                    transaction_type='OUT',
                    quantity=qty,
                    notes=f'Mock order #{order.id} seeded',
                )

            order.total_amount = total
            order.save(update_fields=['total_amount', 'updated_at'])
        finally:
            post_save.connect(enqueue_order_confirmation_email, sender=Order)
