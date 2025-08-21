from django.contrib import admin
from .models import Socio, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "dni", "categoria", "email", "celular", "fecha_nacimiento", "fecha_alta")
    search_fields = ("nombre", "apellido", "dni", "email")
    list_filter = ("categoria",)