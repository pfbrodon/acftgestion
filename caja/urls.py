from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # Resumen general
    path('', views.resumen_caja_view, name='resumen'),
    
    # Gestión de movimientos
    path('movimientos/', views.MovimientoCajaListView.as_view(), name='movimiento_list'),
    path('movimientos/nuevo/', views.MovimientoCajaCreateView.as_view(), name='movimiento_create'),
    path('movimientos/<int:pk>/editar/', views.MovimientoCajaUpdateView.as_view(), name='movimiento_update'),
    path('movimientos/<int:pk>/eliminar/', views.MovimientoCajaDeleteView.as_view(), name='movimiento_delete'),
]
