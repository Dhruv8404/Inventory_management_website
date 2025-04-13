from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, RegisterTemplateView, LoginTemplateView , ItemViewSet, home 
from .import views
from inventory.views import update_inventory_item
from .views import bill_form, get_item_details, save_bill, bill_page
from django.urls import path
from .views import home, monthly_sales_details,get_top_products, logout_view









router = DefaultRouter()
router.register(r'items', ItemViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('logout/', logout_view, name='logout'),  # 🔗 Logout URL
    path('get_top_products/', get_top_products, name='get_top_products'),
    path("bill_page/", bill_page, name="bill_page"),  # Search without bill number
    path("bill_page/<int:bill_number>/", bill_page, name="bill_page_with_number"),  # Get bill with number
    path('bill/', bill_form, name='bill_form'),
    path('get-item-details/<int:item_id>/', get_item_details, name='get_item_details'),
    path('save-bill/', save_bill, name='save_bill'),    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('register-template/', RegisterTemplateView.as_view(), name='register_template'),
    path('login-template/', LoginTemplateView.as_view(), name='login_template'),
    path('home/', home, name='home'),
    path('monthly-sales/<str:month>/', monthly_sales_details, name='monthly_sales_details'),
    path('add-item/', views.add_inventory_item, name='add_inventory_item'),
    path('inventory-list/', views.inventory_list, name='inventory_list'),  
    path('api/', include(router.urls)),
    path('delete/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('update/<int:item_id>/', update_inventory_item, name='update_inventory_item'),


    
]


