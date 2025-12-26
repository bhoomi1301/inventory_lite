from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views
from django.urls import path

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'dealers', views.DealerViewSet, basename='dealer')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')

urlpatterns = router.urls + [
    path('auth/login/', auth_views.LoginView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', auth_views.RefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', auth_views.logout_view, name='token_logout'),
    path('auth/me/', auth_views.me_view, name='token_me'),
]
