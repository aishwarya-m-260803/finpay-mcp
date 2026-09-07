from django.urls import path
from . import api_views, views

urlpatterns = [
    # HTML Dashboard View
    path('', views.home, name='home'),

    # REST API Endpoints
    path('api/dashboard/', api_views.api_dashboard_summary, name='api_dashboard_summary'),
    path('api/customers/', api_views.api_customer_list, name='api_customer_list'),
    path('api/accounts/', api_views.api_account_list, name='api_account_list'),
    path('api/transactions/', api_views.api_transaction_list, name='api_transaction_list'),
    path('api/chat/', api_views.api_chat, name='api_chat'),
]
