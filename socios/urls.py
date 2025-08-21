from django.urls import path
from .views import SocioListView, SocioCreateView, SocioUpdateView, SocioDeleteView

app_name = 'socios'

urlpatterns = [
    path('', SocioListView.as_view(), name='listar'),
    path('nuevo/', SocioCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', SocioUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', SocioDeleteView.as_view(), name='eliminar'),
]
