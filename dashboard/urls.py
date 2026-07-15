from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_cheque, name='upload_cheque'),
    path('queue/', views.queue, name='queue'),
    path('cheque/<uuid:cheque_id>/', views.cheque_detail, name='cheque_detail'),
]
