from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('order-summary/', views.OrderSummary.as_view(), name="order-summary"),
    path('confirm-order/', views.ConfirmOrder.as_view(), name="confirm-order"),
    path('payment/', views.PaymentView.as_view(), name="payment"),
    path('create-payment-intent/', views.create_payment, name="create-payment-intent"),
    path('payment-intent-webhook/', views.payment_intent_webhook, name="payment-intent-webhook"),
    path('create-payment-bit/', views.create_pay_confirmed_bit, name="create-payment-bit"),
    path('btn-go-back-clicked/', views.btn_go_back_clicked, name="btn-go-back-clicked"),
    path('apply-coupon-code/', views.apply_coupon_code, name="apply-coupon-code"),
    path('checkout/<int:plan_id>/<str:coupon_code>/', views.direct_checkout_view, name="checkout"),
    path('direct-payment-intent/', views.direct_payment_intent, name="direct-payment-intent"),
    path('payment-type-change/', views.payment_type_change_view, name="payment-type-change"),
]
