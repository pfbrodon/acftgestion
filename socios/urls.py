from django.urls import path
from .views import (
    SocioListView, SocioCreateView, SocioUpdateView, SocioDeleteView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView
)

app_name = 'socios'

urlpatterns = [
    # URLs para socios
    path('', SocioListView.as_view(), name='listar'),
    path('nuevo/', SocioCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', SocioUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', SocioDeleteView.as_view(), name='eliminar'),
    
    # URLs para categorias
    path('categorias/', CategoriaListView.as_view(), name='listar_categorias'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='crear_categoria'),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', CategoriaDeleteView.as_view(), name='eliminar_categoria'),
]
