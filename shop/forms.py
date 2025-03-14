from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Product, Order, Category, PromoCode
from django.utils.text import slugify
import uuid

class ProductForm(forms.ModelForm):
    """
    Form for creating and updating shop products with improved validation and field customization.
    """
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price',
            'discount_price', 'image', 'stock', 'status', 'featured'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'aria-label': 'Select category'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your product in detail'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Leave empty if no discount'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Available quantity'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'category': _('Product Category'),
            'name': _('Product Name'),
            'description': _('Description'),
            'price': _('Regular Price ($)'),
            'discount_price': _('Sale Price ($)'),
            'stock': _('Stock Quantity'),
            'status': _('Product Status'),
            'image': _('Product Image'),
            'featured': _('Feature this product')
        }
        help_texts = {
            'name': _('Choose a descriptive name (maximum 200 characters)'),
            'price': _('Set the regular price in USD'),
            'discount_price': _('Optional: Set a discounted price lower than the regular price'),
            'stock': _('Enter the quantity available for sale'),
            'status': _('Draft: not visible to customers, Active: available for purchase, Inactive: temporarily unavailable'),
            'featured': _('Featured products appear on the homepage and receive more visibility'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the category field required and populate with all categories
        self.fields['category'].required = True
        self.fields['category'].empty_label = _("Select a category")
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        
        # Mark required fields
        for field_name in self.fields:
            if self.fields[field_name].required:
                self.fields[field_name].label = f"{self.fields[field_name].label} *"
        
        # Add custom error messages
        self.fields['price'].error_messages = {
            'min_value': _('Price must be greater than zero.'),
            'required': _('Please enter a price for your product.')
        }
        self.fields['name'].error_messages = {
            'required': _('Please enter a name for your product.')
        }

    def clean_name(self):
        """
        Validate and clean the product name.
        """
        name = self.cleaned_data.get('name')
        if name:
            # Check if there's an existing product with the same slug
            slug = slugify(name)
            if not self.instance.pk:  # New product
                if Product.objects.filter(slug=slug).exists():
                    raise forms.ValidationError(
                        _('A product with a similar name already exists. Please choose a different name.')
                    )
            else:  # Editing existing product
                if Product.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(
                        _('A product with a similar name already exists. Please choose a different name.')
                    )
        return name

    def clean(self):
        """
        Cross-field validation and additional checks.
        """
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        status = cleaned_data.get('status')
        stock = cleaned_data.get('stock')
        
        # If there's a discount price, ensure it's less than the regular price
        if price and discount_price and discount_price >= price:
            self.add_error('discount_price', _('Discount price must be less than regular price'))
        
        # Warn if setting a product as active with zero stock
        if status == 'active' and stock == 0:
            self.add_error('stock', _('Warning: You are setting this product as active but it has zero stock.'))
        
        return cleaned_data

    def save(self, commit=True):
        """
        Override save method to generate slug from name if needed
        """
        instance = super().save(commit=False)
        
        # Generate slug if it doesn't exist
        if not instance.slug:
            instance.slug = slugify(instance.name)
            
            # Ensure slug is unique
            if Product.objects.filter(slug=instance.slug).exists():
                instance.slug = f"{instance.slug}-{str(uuid.uuid4())[:8]}"
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class OrderCreateForm(forms.ModelForm):
    """
    Form for creating new orders with additional validation and field customization.
    """
    promo_code = forms.CharField(
        required=False,
        label=_('Promo Code'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter promo code (if available)')
        })
    )
    
    class Meta:
        model = Order
        fields = ['quantity', 'shipping_address', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'value': '1'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter your complete shipping address')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Add any special instructions or notes (optional)')
            }),
        }
        labels = {
            'quantity': _('Quantity'),
            'shipping_address': _('Shipping Address'),
            'notes': _('Order Notes')
        }
        help_texts = {
            'shipping_address': _('Please provide your full address including street, city, state/province, postal code, and country'),
            'notes': _('Special delivery instructions or other information for this order')
        }

    def __init__(self, product=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        
        # Set max quantity based on product stock
        if product:
            max_stock = product.stock
            self.fields['quantity'].widget.attrs['max'] = max_stock
            if max_stock < 10:
                self.fields['quantity'].help_text = _('Limited stock available! Only {0} remaining.'.format(max_stock))
                if max_stock < 5:
                    self.fields['quantity'].help_text = _('Very low stock! Only {0} remaining.'.format(max_stock))
        
        # Make shipping address required
        self.fields['shipping_address'].required = True
        
        # Mark required fields
        for field_name in self.fields:
            if self.fields[field_name].required:
                self.fields[field_name].label = f"{self.fields[field_name].label} *"

    def clean_quantity(self):
        """
        Validate the quantity against product stock
        """
        quantity = self.cleaned_data.get('quantity')
        if self.product and quantity > self.product.stock:
            raise forms.ValidationError(
                _('Requested quantity ({0}) exceeds available stock ({1})').format(
                    quantity, self.product.stock
                )
            )
        return quantity

    def clean_shipping_address(self):
        """
        Validate the shipping address
        """
        address = self.cleaned_data.get('shipping_address')
        if address and len(address.strip()) < 10:
            raise forms.ValidationError(
                _('Please provide a complete shipping address')
            )
        return address


class ProductSearchForm(forms.Form):
    """
    Form for searching and filtering products
    """
    query = forms.CharField(
        required=False,
        label=_('Search'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search products...'),
            'aria-label': _('Search')
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        empty_label=_('All Categories'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('Filter by category')
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        label=_('Min Price'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Min $'),
            'min': '0',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        label=_('Max Price'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Max $'),
            'min': '0',
            'step': '0.01'
        })
    )
    
    in_stock_only = forms.BooleanField(
        required=False,
        label=_('In Stock Only'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Default Sorting')),
            ('price_asc', _('Price: Low to High')),
            ('price_desc', _('Price: High to Low')),
            ('name_asc', _('Name: A to Z')),
            ('name_desc', _('Name: Z to A')),
            ('newest', _('Newest First')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('Sort products')
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            self.add_error('min_price', 
                _('Minimum price cannot be greater than maximum price')
            )
            
        return cleaned_data


class PromoCodeForm(forms.ModelForm):
    """
    Form for managing promotional codes
    """
    class Meta:
        model = PromoCode
        fields = [
            'code', 'description', 'discount_type', 'discount_value',
            'min_purchase_amount', 'max_discount_amount', 'uses_limit',
            'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter promo code')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Describe this promotional offer')
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01'
            }),
            'min_purchase_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': _('Minimum purchase amount (optional)')
            }),
            'max_discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': _('Maximum discount amount (optional)')
            }),
            'uses_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': _('Maximum number of uses (optional)')
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate percentage discount value
        if discount_type == 'percentage' and discount_value and discount_value > 100:
            self.add_error('discount_value', _('Percentage discount cannot exceed 100%'))
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _('End date must be after start date'))
            
        return cleaned_data