from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Product URLs
    path('', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<uuid:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('products/<uuid:product_pk>/order/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<uuid:pk>/cancel/', views.cancel_order, name='order_cancel'),
    
    # Cart URLs (new)
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<uuid:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Category URLs
    path('category/<slug:slug>/', views.ProductListView.as_view(), name='category_products'),
    
    # API endpoints
    path('api/cart/update/', views.update_cart_ajax, name='update_cart_ajax'),
    path('api/stock/<uuid:product_id>/check/', views.check_stock, name='check_stock'),
]