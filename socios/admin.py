from django.contrib import admin
from .models import Socio

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
	list_display = ("nombre_apellido", "dni", "categoria", "email", "celular", "fecha_nacimiento", "fecha_alta")
	search_fields = ("nombre_apellido", "dni", "email")
	list_filter = ("categoria",)
