# shop/context_processors.py

from .models import Product

def featured_products(request):
    featured_products = Product.objects.filter(
        featured=True,
        status='active'
    ).select_related(
        'category'
    ).order_by(
        '-created_on'
    )[:4]
    
    return {'featured_products': featured_products}