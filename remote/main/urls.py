from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout, name='logout'),
    path('pnet', views.pnet, name='pnet'),

    path('devs_update', views.devs_update, name='devs_update'),
    path('telnet', views.telnet, name='telnet'),
    path('telnet_cmd_hist', views.telnet_cmd_hist, name='telnet_cmd_hist'),
    path('devices_page', views.devices_page, name='devices_page'),
    path('telnet_read_new', views.telnet_read_new, name='telnet_read_new'),
    path('telnet_write_new', views.telnet_write_new, name='telnet_write_new'),

    path('database', views.knowledge_base, name='database'),

]

