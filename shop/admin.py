from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, Order

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Product, Order, PromoCode, AffiliateMarketing, AffiliateTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'seller',
        'category',
        'display_price',
        'display_discount',
        'stock',
        'status',
        'featured',
        'display_image',
        'created_on'
    )
    list_filter = (
        'status',
        'featured',
        'category',
        'created_on',
        ('seller', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('name', 'description', 'seller__username')
    readonly_fields = ('created_on', 'updated_on')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('seller',)
    list_editable = ('status', 'featured', 'stock')
    list_per_page = 20
    date_hierarchy = 'created_on'

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('seller', 'name', 'slug', 'category', 'description')
        }),
        (_('Pricing and Stock'), {
            'fields': ('price', 'discount_price', 'stock')
        }),
        (_('Media'), {
            'fields': ('image',)
        }),
        (_('Status'), {
            'fields': ('status', 'featured')
        }),
        (_('Timestamps'), {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    def display_price(self, obj):
        if obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through">${}</span> '
                '<span style="color: red">${}</span>',
                obj.price,
                obj.discount_price
            )
        return f'${obj.price}'
    display_price.short_description = _('Price')

    def display_discount(self, obj):
        if obj.discount_price:
            discount_percentage = ((obj.price - obj.discount_price) / obj.price) * 100
            return format_html(
            '<span style="color: green">-{}%</span>',
            '{:.1f}'.format(discount_percentage)
        )
        return ''
    display_discount.short_description = _('Discount')


    def display_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url
            )
        return _('No image')
    display_image.short_description = _('Image')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer_link',
        'product_link',
        'quantity',
        'total_price',
        'promo_code_display',
        'status',
        'payment_status',
        'created_on'
    )
    list_filter = (
        'status',
        'payment_status',
        'created_on',
        ('buyer', admin.RelatedOnlyFieldListFilter),
        ('promo_code', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'id',
        'buyer__username',
        'buyer__email',
        'product__name',
        'tracking_number',
        'promo_code__code'
    )
    readonly_fields = (
        'id',
        'unit_price',
        'total_price',
        'promo_code_discount',
        'created_on',
        'updated_on'
    )
    raw_id_fields = ('buyer', 'product', 'promo_code')
    list_per_page = 20
    date_hierarchy = 'created_on'

    fieldsets = (
        (_('Order Information'), {
            'fields': ('id', 'buyer', 'product', 'quantity', 'promo_code')
        }),
        (_('Financial Details'), {
            'fields': (
                'unit_price', 
                'total_price', 
                'promo_code_discount', 
                'payment_status'
            )
        }),
        (_('Order Status'), {
            'fields': ('status', 'tracking_number')
        }),
        (_('Shipping'), {
            'fields': ('shipping_address',)
        }),
        (_('Additional Information'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    def buyer_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.buyer.id])
        return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
    buyer_link.short_description = _('Buyer')
    buyer_link.admin_order_field = 'buyer__username'

    def product_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = _('Product')
    product_link.admin_order_field = 'product__name'

    def promo_code_display(self, obj):
        return obj.promo_code.code if obj.promo_code else '-'
    promo_code_display.short_description = _('Promo Code')
    promo_code_display.admin_order_field = 'promo_code__code'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'product', 'promo_code')

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of orders that are not pending
        if obj and obj.status != 'pending':
            return False
        return super().has_delete_permission(request, obj)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'discount_type', 
        'discount_value', 
        'is_active', 
        'current_uses', 
        'uses_limit',
        'start_date', 
        'end_date'
    )
    list_filter = (
        'is_active', 
        'discount_type', 
        'start_date', 
        'end_date'
    )
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_on', 'updated_on')
    filter_horizontal = ('applicable_products', 'applicable_categories')

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('code', 'description', 'is_active')
        }),
        (_('Discount Details'), {
            'fields': ('discount_type', 'discount_value', 'min_purchase_amount', 'max_discount_amount')
        }),
        (_('Usage Limits'), {
            'fields': ('uses_limit', 'current_uses', 'start_date', 'end_date')
        }),
        (_('Restrictions'), {
            'fields': ('applicable_products', 'applicable_categories')
        }),
        (_('Timestamps'), {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AffiliateMarketing)
class AffiliateMarketingAdmin(admin.ModelAdmin):
    list_display = (
        'affiliate', 
        'unique_code', 
        'commission_type', 
        'commission_rate', 
        'is_active', 
        'total_referrals', 
        'total_commission_earned'
    )
    list_filter = (
        'is_active', 
        'commission_type', 
        'created_on'
    )
    search_fields = ('affiliate__username', 'unique_code')
    readonly_fields = (
        'total_referrals', 
        'total_commission_earned', 
        'created_on', 
        'updated_on'
    )

    fieldsets = (
        (_('Affiliate Information'), {
            'fields': ('affiliate', 'unique_code', 'is_active')
        }),
        (_('Commission Details'), {
            'fields': ('commission_type', 'commission_rate')
        }),
        (_('Performance Metrics'), {
            'fields': ('total_referrals', 'total_commission_earned')
        }),
        (_('Timestamps'), {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AffiliateTransaction)
class AffiliateTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'affiliate_program', 
        'order', 
        'commission_amount', 
        'created_on'
    )
    list_filter = ('created_on',)
    search_fields = (
        'affiliate_program__unique_code', 
        'order__id'
    )
    readonly_fields = ('created_on',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'affiliate_program', 
            'affiliate_program__affiliate', 
            'order'
        )

# Optional: Custom Admin Site Configuration
class EcommerceAdminSite(admin.AdminSite):
    site_header = 'E-commerce Administration'
    site_title = 'E-commerce Admin Portal'
    index_title = 'E-commerce Management'

# Uncomment these lines if you want to use a custom admin site
# admin_site = EcommerceAdminSite(name='ecommerce_admin')
# admin_site.register(Category, CategoryAdmin)
# admin_site.register(Product, ProductAdmin)
# admin_site.register(Order, OrderAdmin)
# admin_site.register(PromoCode, PromoCodeAdmin)
# admin_site.register(AffiliateMarketing, AffiliateMarketingAdmin)
# admin_site.register(AffiliateTransaction, AffiliateTransactionAdmin)