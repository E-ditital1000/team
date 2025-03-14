from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid













from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

User = get_user_model()

class PromoCode(models.Model):
    """
    Represents a promotional code that can be applied to orders
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Optional constraints
    min_purchase_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Usage limitations
    uses_limit = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text=_("Maximum number of times this promo code can be used")
    )
    current_uses = models.PositiveIntegerField(default=0)
    
    # Validity period
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Optional product/category restrictions
    applicable_products = models.ManyToManyField(
        'Product', 
        blank=True, 
        related_name='eligible_promo_codes'
    )
    applicable_categories = models.ManyToManyField(
        'Category', 
        blank=True, 
        related_name='eligible_promo_codes'
    )
    
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate discount value based on type
        if self.discount_type == 'percentage' and self.discount_value > 100:
            raise ValidationError(_('Percentage discount cannot exceed 100%'))
        
        # Validate date range
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_('End date must be after start date'))

    def is_valid(self, order_total=None, product=None, category=None):
        """
        Check if promo code is valid for a specific order
        """
        from django.utils import timezone
        now = timezone.now()

        # Check active status
        if not self.is_active:
            return False

        # Check usage limit
        if self.uses_limit and self.current_uses >= self.uses_limit:
            return False

        # Check date range
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False

        # Check minimum purchase amount
        if self.min_purchase_amount and order_total and order_total < self.min_purchase_amount:
            return False

        # Check product/category restrictions
        if self.applicable_products.exists() and product and product not in self.applicable_products.all():
            return False
        if self.applicable_categories.exists() and category and category not in self.applicable_categories.all():
            return False

        return True

    def calculate_discount(self, total_amount):
        """
        Calculate the discount amount
        """
        if self.discount_type == 'percentage':
            discount = total_amount * (self.discount_value / 100)
        else:
            discount = self.discount_value

        # Apply max discount limit if set
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)

        return discount

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"




User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from decimal import Decimal
import uuid

User = get_user_model()

class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="products"
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        related_name="products",
        null=True
    )
    name = models.CharField(
        max_length=200,
        help_text=_("Name of the product")
    )
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(
        blank=True,
        help_text=_("Details about the product")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Price of the product"),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    image = models.ImageField(
        upload_to='product_images/%Y/%m/',
        blank=True,
        null=True
    )
    stock = models.PositiveIntegerField(
        default=0,
        help_text=_("Available quantity")
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    featured = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['created_on']),
        ]

    def clean(self):
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError(
                _('Discount price must be less than regular price')
            )

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            original_slug = slugify(self.name)
            queryset = Product.objects.all()
            
            # If this is an update, exclude the current instance
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
                
            slug = original_slug
            counter = 1
            
            # Ensure slug is unique
            while queryset.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
                
            self.slug = slug
            
        super().save(*args, **kwargs)

    def get_current_price(self):
        return self.discount_price if self.discount_price else self.price

    def is_in_stock(self):
        return self.stock > 0 and self.status == 'active'

    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    shipping_address = models.TextField()
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    promo_code = models.ForeignKey(
    PromoCode, 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    related_name='orders'
    )
    promo_code_discount = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=Decimal('0.00')
    )
    notes = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_on']),
        ]

    
def save(self, *args, **kwargs):
    if not self.unit_price:
        self.unit_price = self.product.get_current_price()
    
    # Calculate base total price
    self.total_price = self.unit_price * self.quantity
    
    # Apply promo code discount if applicable
    if self.promo_code and self.promo_code.is_valid(
        order_total=self.total_price, 
        product=self.product, 
        category=self.product.category
    ):
        self.promo_code_discount = self.promo_code.calculate_discount(self.total_price)
        self.total_price -= self.promo_code_discount
        
        # Increment promo code uses
        self.promo_code.current_uses += 1
        self.promo_code.save()

    super().save(*args, **kwargs)
    
    def clean(self):
        if self.quantity > self.product.stock:
            raise ValidationError(
                _('Order quantity exceeds available stock')
            )

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.get_current_price()
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        self.payment_status = 'paid'
        self.save()
        
    def mark_as_shipped(self, tracking_number=None):
        if tracking_number:
            self.tracking_number = tracking_number
        self.status = 'shipped'
        self.save()

    def can_cancel(self):
        return self.status in ['pending', 'processing']
    
    

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username}"



class AffiliateMarketing(models.Model):
    """
    Represents an affiliate marketing program
    """
    COMMISSION_TYPE_CHOICES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]

    affiliate = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="affiliate_programs"
    )
    unique_code = models.CharField(max_length=50, unique=True)
    commission_type = models.CharField(
        max_length=20, 
        choices=COMMISSION_TYPE_CHOICES, 
        default='percentage'
    )
    commission_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True)
    
    total_referrals = models.PositiveIntegerField(default=0)
    total_commission_earned = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def calculate_commission(self, order_total):
        """
        Calculate commission for an order
        """
        if self.commission_type == 'percentage':
            commission = order_total * (self.commission_rate / 100)
        else:
            commission = self.commission_rate

        return commission

    def record_referral(self, order):
        """
        Record a successful referral and update affiliate stats
        """
        self.total_referrals += 1
        commission = self.calculate_commission(order.total_price)
        self.total_commission_earned += commission
        self.save()

        # Optionally create an AffiliateTransaction record
        AffiliateTransaction.objects.create(
            affiliate_program=self,
            order=order,
            commission_amount=commission
        )

    def __str__(self):
        return f"Affiliate {self.affiliate.username} - {self.unique_code}"

class AffiliateTransaction(models.Model):
    """
    Tracks individual affiliate transactions
    """
    affiliate_program = models.ForeignKey(
        AffiliateMarketing, 
        on_delete=models.CASCADE, 
        related_name="transactions"
    )
    order = models.ForeignKey(
        'Order', 
        on_delete=models.CASCADE, 
        related_name="affiliate_transactions"
    )
    commission_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction for {self.affiliate_program.unique_code} - Order {self.order.id}"