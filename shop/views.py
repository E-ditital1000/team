from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, F, Sum
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from decimal import Decimal

from .models import Product, Order, Category, PromoCode
from .forms import ProductForm, OrderCreateForm, ProductSearchForm
from bloger.models import UserProfile  # Import UserProfile from users app

# Product Views
class ProductListView(FormMixin, ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    form_class = ProductSearchForm

    def get_queryset(self):
        queryset = Product.objects.filter(status='active')
        form = self.get_form()
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            category = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            in_stock_only = form.cleaned_data.get('in_stock_only')
                
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                )
            if category:
                queryset = queryset.filter(category=category)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            if in_stock_only:
                queryset = queryset.filter(stock__gt=0)
                
        return queryset.select_related('seller', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_products'] = Product.objects.filter(
            featured=True,
            status='active'
        )[:4]
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Product.objects.select_related('seller', 'category'),
            slug=self.kwargs['slug']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_form'] = OrderCreateForm(product=self.object)
        
        # Get related products (same category, excluding current)
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            status='active'
        ).exclude(id=self.object.id)[:4]
        
        # Calculate discount percentage if applicable
        if self.object.discount_price and self.object.price:
            discount_percentage = 100 - (self.object.discount_price / self.object.price * 100)
            context['discount_percentage'] = int(discount_percentage)
        
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, _('Product created successfully!'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.object.slug})

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    
    def test_func(self):
        return self.get_object().seller == self.request.user
    
    def get_success_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        messages.success(self.request, _('Product updated successfully!'))
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'shop/product_confirm_delete.html'
    success_url = reverse_lazy('shop:product_list')
    
    def test_func(self):
        return self.get_object().seller == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Product deleted successfully!'))
        return super().delete(request, *args, **kwargs)

# Order Views
import logging

logger = logging.getLogger(__name__)

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'shop/order_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get product using UUID
        self.product = get_object_or_404(Product, id=self.kwargs['product_pk'])
        kwargs['product'] = self.product
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add product to context
        context['product'] = self.product
        
        # Calculate subtotal based on form quantity or default to 1
        quantity = 1
        if self.request.method == 'POST':
            quantity = int(self.request.POST.get('quantity', 1))
        elif hasattr(self, 'form') and hasattr(self.form, 'cleaned_data'):
            quantity = self.form.cleaned_data.get('quantity', 1)
            
        context['subtotal'] = self.product.get_current_price() * quantity
        
        return context
    
    def form_valid(self, form):
        if not self.product.is_in_stock():
            messages.error(self.request, _('Sorry, this product is out of stock.'))
            if self.product.slug:
                return redirect('shop:product_detail', slug=self.product.slug)
            else:
                return redirect('shop:product_list')
            
        try:
            with transaction.atomic():
                form.instance.buyer = self.request.user
                form.instance.product = self.product
                form.instance.unit_price = self.product.get_current_price()
                form.instance.total_price = form.instance.unit_price * form.cleaned_data['quantity']
                
                # Attempt to reduce stock
                if not self.product.reduce_stock(form.cleaned_data['quantity']):
                    messages.error(self.request, _('Sorry, insufficient stock available.'))
                    if self.product.slug:
                        return redirect('shop:product_detail', slug=self.product.slug)
                    else:
                        return redirect('shop:product_list')
                
                # Process promo code if provided
                promo_code = form.cleaned_data.get('promo_code')
                if promo_code:
                    try:
                        from .models import PromoCode
                        try:
                            promo = PromoCode.objects.get(code=promo_code, is_active=True)
                            if promo.is_valid(
                                order_total=form.instance.total_price,
                                product=self.product,
                                category=self.product.category
                            ):
                                discount = promo.calculate_discount(form.instance.total_price)
                                form.instance.promo_code = promo
                                form.instance.promo_code_discount = discount
                                form.instance.total_price -= discount
                                promo.current_uses += 1
                                promo.save()
                                messages.success(self.request, _('Promo code applied successfully!'))
                            else:
                                messages.warning(self.request, _('This promo code is not valid for your order.'))
                        except PromoCode.DoesNotExist:
                            messages.warning(self.request, _('Invalid promo code.'))
                    except Exception as e:
                        logger.error(f"Error applying promo code: {str(e)}")
                        messages.warning(self.request, _('Unable to apply promo code.'))
                
                response = super().form_valid(form)
                
                # Send notifications to seller
                notification_info = self.send_seller_notifications(form.instance)
                
                # Add notification details to success message
                success_msg = _('Order placed successfully!')
                if notification_info:
                    if notification_info.get('email_sent'):
                        success_msg += _(' An email notification has been sent to the seller.')
                    if notification_info.get('whatsapp_sent'):
                        success_msg += _(' A WhatsApp notification has been sent to the seller.')
                    elif notification_info.get('whatsapp_url'):
                        # In case we're just generating a URL and not sending directly
                        success_msg += _(' The seller will be notified about your order.')
                
                messages.success(self.request, success_msg)
                return response
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            messages.error(self.request, _('An error occurred while processing your order. Please try again.'))
            if self.product.slug:
                return redirect('shop:product_detail', slug=self.product.slug)
            else:
                return redirect('shop:product_list')
    
    def send_seller_notifications(self, order):
        """
        Send WhatsApp message and email to the seller based on their preferences
        Returns dict with notification status
        """
        seller = order.product.seller
        notification_info = {
            'email_sent': False,
            'whatsapp_sent': False,
            'whatsapp_url': None
        }
        
        try:
            # Get seller's profile
            profile = getattr(seller, 'profile', None)
            if not profile:
                # Create a profile if it doesn't exist
                profile = UserProfile.objects.create(user=seller)
                logger.info(f"Created new profile for seller {seller.username}")
            
            # Send notifications based on seller preferences
            # WhatsApp notification
            if profile.receive_order_whatsapp:
                whatsapp_number = None
                
                # Try to get WhatsApp number, falling back to regular phone if needed
                if hasattr(profile, 'get_formatted_whatsapp') and callable(getattr(profile, 'get_formatted_whatsapp')):
                    whatsapp_number = profile.get_formatted_whatsapp()
                elif hasattr(profile, 'whatsapp_phone') and profile.whatsapp_phone:
                    whatsapp_number = ''.join(filter(str.isdigit, profile.whatsapp_phone))
                elif hasattr(profile, 'phone') and profile.phone:
                    whatsapp_number = ''.join(filter(str.isdigit, profile.phone))
                
                if whatsapp_number:
                    whatsapp_url = self.send_whatsapp_notification(whatsapp_number, order)
                    if whatsapp_url:
                        notification_info['whatsapp_url'] = whatsapp_url
                        notification_info['whatsapp_sent'] = True
                else:
                    logger.warning(f"Seller {seller.username} has WhatsApp notifications enabled but no phone number.")
            
            # Email notification
            if profile.receive_order_emails or not hasattr(profile, 'receive_order_emails'):
                # Default to sending email if the preference field doesn't exist
                if seller.email:
                    self.send_email_notification(seller.email, order)
                    notification_info['email_sent'] = True
            
            return notification_info
                
        except Exception as e:
            # Log the error but don't stop the order process
            logger.error(f"Failed to send seller notifications: {str(e)}")
            return notification_info
    
    def send_whatsapp_notification(self, phone_number, order):
        """Send WhatsApp message using WhatsApp click-to-chat URL"""
        # Format phone number (remove any spaces, dashes, etc.)
        formatted_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Ensure number starts with country code
        if not formatted_phone.startswith('+'):
            # You might want to set a default country code based on your location
            formatted_phone = '+' + formatted_phone
        
        # Create message content
        message = f"""
*New Order Notification!*

Order ID: {order.id}
Product: {order.product.name}
Quantity: {order.quantity}
Total Price: ${order.total_price}
Customer: {order.buyer.username}

*Shipping Address:*
{order.shipping_address}

Please process this order as soon as possible.
"""
        
        # URL encode the message
        encoded_message = urllib.parse.quote(message)
        
        # Create WhatsApp API URL
        whatsapp_url = f"https://api.whatsapp.com/send?phone={formatted_phone}&text={encoded_message}"
        
        try:
            # For a more integrated approach with direct sending, you would use
            # WhatsApp Business API or a service like Twilio
            
            # Log the WhatsApp URL for debugging/tracking
            logger.info(f"WhatsApp notification URL for {formatted_phone}: {whatsapp_url}")
            
            return whatsapp_url
        except Exception as e:
            logger.error(f"WhatsApp notification failed: {str(e)}")
            return None
    
    def send_email_notification(self, email, order):
        """Send email notification to seller"""
        subject = f'New Order: #{order.id} - {order.product.name}'
        
        # Get site domain for complete URLs in the email
        try:
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            site_url = f"https://{current_site.domain}"
        except:
            # Fallback if sites framework is not configured
            from django.conf import settings
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        
        # Create email context
        context = {
            'order': order,
            'product': order.product,
            'buyer': order.buyer,
            'site_url': site_url,
        }
        
        # Render email content from template
        try:
            html_message = render_to_string('shop/emails/new_order_notification.html', context)
            plain_message = strip_tags(html_message)
        except Exception as e:
            logger.error(f"Error rendering email template: {str(e)}")
            # Fallback to basic text email if template rendering fails
            plain_message = f"""
New Order Notification!

Order ID: {order.id}
Product: {order.product.name}
Quantity: {order.quantity}
Total Price: ${order.total_price}
Customer: {order.buyer.username}

Shipping Address:
{order.shipping_address}

Please process this order as soon as possible.
            """
            html_message = None
        
        try:
            # Send email
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            send_mail(
                subject,
                plain_message,
                from_email,  # From email
                [email],  # To email
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Order notification email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            return False
    
    def get_success_url(self):
        return reverse('shop:order_detail', kwargs={'pk': self.object.pk})

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'shop/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related(
            'product', 'buyer'
        ).order_by('-created_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add statistics
        orders = self.get_queryset()
        context['total_spent'] = orders.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        context['total_orders'] = orders.count()
        context['pending_orders'] = orders.filter(
            status__in=['pending', 'processing']
        ).count()
        context['completed_orders'] = orders.filter(
            status__in=['delivered', 'shipped']
        ).count()
        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'shop/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('product', 'buyer', 'promo_code')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.buyer != self.request.user:
            raise PermissionDenied
        return obj

# Cart Management Views
@login_required
def add_to_cart(request, product_id):
    """
    Add a product to the cart or update its quantity if already in cart
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        # Check stock availability
        if quantity > product.stock:
            messages.error(request, _('Requested quantity exceeds available stock.'))
            if product.slug:
                return redirect('shop:product_detail', slug=product.slug)
            else:
                return redirect('shop:product_list')
            
        # Get or initialize cart
        cart = request.session.get('cart', {})
        
        # Update cart
        if str(product_id) in cart:
            cart[str(product_id)] += quantity
        else:
            cart[str(product_id)] = quantity
            
        # Ensure quantity doesn't exceed stock
        if cart[str(product_id)] > product.stock:
            cart[str(product_id)] = product.stock
            messages.warning(request, _(f'Quantity adjusted to maximum available stock ({product.stock}).'))
        
        # Save updated cart to session
        request.session['cart'] = cart
        messages.success(request, _(f'{product.name} added to cart'))
        
        # Redirect based on next parameter or to cart by default
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('shop:cart')
        
    else:
        messages.error(request, _('Invalid request method.'))
        return redirect('shop:product_list')

@login_required
def cart_view(request):
    """
    Display the current cart contents
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    if not cart:
        messages.info(request, _('Your cart is empty.'))
        return render(request, 'shop/cart.html', {
            'cart_items': [],
            'total': total
        })
    
    # Calculate cart items and total
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            price = product.get_current_price()
            subtotal = price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            # Remove invalid products from cart
            del cart[product_id]
            request.session['cart'] = cart
    
    # Process promo code if submitted
    if request.method == 'POST':
        promo_code = request.POST.get('promo_code')
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code, is_active=True)
                if promo.is_valid(order_total=total):
                    discount = promo.calculate_discount(total)
                    request.session['promo_code'] = {
                        'code': promo_code,
                        'discount': str(discount)
                    }
                    messages.success(request, _(f'Promo code applied! You saved ${discount}.'))
                else:
                    messages.warning(request, _('This promo code is not valid for your current cart.'))
            except PromoCode.DoesNotExist:
                messages.warning(request, _('Invalid promo code.'))
            
            return redirect('shop:cart')
    
    # Apply saved promo code if exists
    promo_info = request.session.get('promo_code')
    discount = Decimal('0.00')
    if promo_info:
        discount = Decimal(promo_info['discount'])
        total -= discount
    
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'final_total': total - discount,
        'promo_code': promo_info['code'] if promo_info else ''
    })

@login_required
def update_cart_item(request, product_id):
    """
    Update the quantity of a cart item
    """
    if request.method != 'POST':
        return redirect('shop:cart')
    
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str not in cart:
        messages.error(request, _('Product not found in your cart.'))
        return redirect('shop:cart')
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            del cart[product_id_str]
            messages.success(request, _('Item removed from cart.'))
        else:
            # Check stock availability
            product = get_object_or_404(Product, id=product_id)
            if quantity > product.stock:
                quantity = product.stock
                messages.warning(request, _(f'Quantity adjusted to maximum available stock ({product.stock}).'))
            
            cart[product_id_str] = quantity
            messages.success(request, _('Cart updated successfully.'))
        
        request.session['cart'] = cart
    except ValueError:
        messages.error(request, _('Invalid quantity.'))
    
    return redirect('shop:cart')

@login_required
def remove_from_cart(request, product_id):
    """
    Remove an item from the cart
    """
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        product = get_object_or_404(Product, id=product_id)
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, _(f'{product.name} removed from cart.'))
    
    return redirect('shop:cart')

@login_required
def clear_cart(request):
    """
    Clear all items from the cart
    """
    if 'cart' in request.session:
        request.session['cart'] = {}
        if 'promo_code' in request.session:
            del request.session['promo_code']
        messages.success(request, _('Your cart has been cleared.'))
    
    return redirect('shop:cart')

@login_required
def checkout(request):
    """
    Process cart checkout to create order
    """
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, _('Your cart is empty.'))
        return redirect('shop:cart')
    
    # Get cart total
    cart_items = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            price = product.get_current_price()
            subtotal = price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            # Remove invalid products from cart
            del cart[product_id]
    
    # Apply promo code if exists
    promo_info = request.session.get('promo_code')
    discount = Decimal('0.00')
    promo_code = None
    
    if promo_info:
        try:
            promo_code = PromoCode.objects.get(code=promo_info['code'], is_active=True)
            if promo_code.is_valid(order_total=total):
                discount = Decimal(promo_info['discount'])
            else:
                del request.session['promo_code']
                promo_code = None
                messages.warning(request, _('The previously applied promo code is no longer valid.'))
        except PromoCode.DoesNotExist:
            del request.session['promo_code']
            messages.warning(request, _('The previously applied promo code is no longer valid.'))
    
    final_total = total - discount
    
    if request.method == 'POST':
        # Create an order for each product in cart
        try:
            with transaction.atomic():
                for item in cart_items:
                    product = item['product']
                    quantity = item['quantity']
                    
                    # Ensure product is still in stock
                    if not product.is_in_stock() or product.stock < quantity:
                        messages.error(request, 
                            _(f'Sorry, "{product.name}" is no longer available in the requested quantity. Please update your cart.'))
                        return redirect('shop:cart')
                    
                    # Create order
                    order = Order(
                        buyer=request.user,
                        product=product,
                        quantity=quantity,
                        unit_price=item['price'],
                        total_price=item['subtotal'],
                        shipping_address=request.POST.get('shipping_address', ''),
                        status='pending',
                        payment_status='pending'
                    )
                    
                    # Apply promo code if applicable
                    if promo_code:
                        item_discount = (item['subtotal'] / total) * discount
                        order.promo_code = promo_code
                        order.promo_code_discount = item_discount
                        order.total_price -= item_discount
                    
                    order.save()
                    
                    # Reduce stock
                    product.reduce_stock(quantity)
                
                # Clear cart and promo code after successful checkout
                request.session['cart'] = {}
                if 'promo_code' in request.session:
                    del request.session['promo_code']
                
                messages.success(request, _('Your order has been placed successfully!'))
                return redirect('shop:order_list')
                
        except Exception as e:
            messages.error(request, _(f'An error occurred during checkout: {str(e)}'))
            return redirect('shop:cart')
    
    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'final_total': final_total,
        'promo_code': promo_info['code'] if promo_info else ''
    })

@login_required
@require_POST
def cancel_order(request, pk):
    """
    Cancel an order that is in pending or processing status
    """
    order = get_object_or_404(Order, pk=pk, buyer=request.user)
    
    if order.status not in ['pending', 'processing']:
        messages.error(request, _('Only pending or processing orders can be cancelled.'))
        return redirect('shop:order_detail', pk=order.pk)
    
    try:
        with transaction.atomic():
            # Return stock to product
            product = order.product
            product.stock += order.quantity
            product.save()
            
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            messages.success(request, _('Order cancelled successfully.'))
    except Exception as e:
        messages.error(request, _(f'Error cancelling order: {str(e)}'))
    
    return redirect('shop:order_list')

# API Views for AJAX functionality
@require_POST
def update_cart_ajax(request):
    """
    Update cart via AJAX request
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            if quantity <= product.stock:
                cart = request.session.get('cart', {})
                cart[str(product_id)] = quantity
                request.session['cart'] = cart
                
                # Calculate new cart totals
                total_items = sum(cart.values())
                total_price = sum(
                    Product.objects.get(id=pid).get_current_price() * qty
                    for pid, qty in cart.items()
                )
                
                return JsonResponse({
                    'status': 'success',
                    'total_items': total_items,
                    'total_price': str(total_price),
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': _('Requested quantity exceeds available stock')
                })
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': _('Product not found')
            })
    return JsonResponse({'status': 'error', 'message': _('Invalid request')})

def check_stock(request, product_id):
    """
    Check product stock via AJAX
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'status': 'success',
                'stock': product.stock,
                'in_stock': product.stock > 0
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': _('Product not found')
            })
    return JsonResponse({'status': 'error', 'message': _('Invalid request')})