from django.urls import path
from .views import (
    SocioListView, SocioCreateView, SocioUpdateView, SocioDeleteView, SocioDetailView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    PagoCreateView, PagoUpdateView, PagoDeleteView, PagoListView,
    ConceptoListView, ConceptoCreateView, ConceptoUpdateView, ConceptoDeleteView,
    CuotaListView, CuotaCreateView, CuotaUpdateView, CuotaDeleteView,
    get_cuota_monto, get_concepto_monto,
    # Vistas de autenticación
    SocioLoginView, SocioLogoutView, RegistroView, MiPerfilView
)

app_name = 'socios'

urlpatterns = [
    # URLs para socios
    path('', SocioListView.as_view(), name='listar'),
    path('nuevo/', SocioCreateView.as_view(), name='crear'),
    path('<int:pk>/', SocioDetailView.as_view(), name='detalle_socio'),
    path('editar/<int:pk>/', SocioUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', SocioDeleteView.as_view(), name='eliminar'),
    
    # URLs para categorias
    path('categorias/', CategoriaListView.as_view(), name='listar_categorias'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='crear_categoria'),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', CategoriaDeleteView.as_view(), name='eliminar_categoria'),
    
    # URLs para pagos
    path('pagos/', PagoListView.as_view(), name='listar_pagos'),
    path('pagos/nuevo/<int:socio_id>/', PagoCreateView.as_view(), name='crear_pago'),
    path('pagos/nuevo/', PagoCreateView.as_view(), name='crear_pago_general'),
    path('pagos/editar/<int:pk>/', PagoUpdateView.as_view(), name='editar_pago'),
    path('pagos/eliminar/<int:pk>/', PagoDeleteView.as_view(), name='eliminar_pago'),
    path('pagos/cuota-monto/', get_cuota_monto, name='get_cuota_monto'),
    
    # URLs para conceptos
    path('conceptos/', ConceptoListView.as_view(), name='listar_conceptos'),
    path('conceptos/nuevo/', ConceptoCreateView.as_view(), name='crear_concepto'),
    path('conceptos/editar/<int:pk>/', ConceptoUpdateView.as_view(), name='editar_concepto'),
    path('conceptos/eliminar/<int:pk>/', ConceptoDeleteView.as_view(), name='eliminar_concepto'),
    path('conceptos/monto/', get_concepto_monto, name='get_concepto_monto'),
    
    # URLs para cuotas
    path('cuotas/', CuotaListView.as_view(), name='listar_cuotas'),
    path('cuotas/nueva/', CuotaCreateView.as_view(), name='crear_cuota'),
    path('cuotas/editar/<int:pk>/', CuotaUpdateView.as_view(), name='editar_cuota'),
    path('cuotas/eliminar/<int:pk>/', CuotaDeleteView.as_view(), name='eliminar_cuota'),
    
    # URLs para autenticación
    path('login/', SocioLoginView.as_view(), name='login'),
    path('logout/', SocioLogoutView.as_view(), name='logout'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
]
