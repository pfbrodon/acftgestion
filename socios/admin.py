from django.contrib import admin
from .models import Socio, Categoria, Pago, Concepto

@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "monto_sugerido", "activo", "descripcion")
    search_fields = ("nombre",)
    list_filter = ("activo",)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    fields = ('fecha_pago', 'mes_correspondiente', 'monto', 'metodo_pago', 'comprobante')

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "dni", "categoria", "email", "celular", "fecha_nacimiento", "fecha_alta", "estado_pagos")
    search_fields = ("nombre", "apellido", "dni", "email")
    list_filter = ("categoria",)
    inlines = [PagoInline]
    
    def estado_pagos(self, obj):
        return obj.get_estado_pagos()
    
    estado_pagos.short_description = "Estado de pagos"

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("socio", "concepto", "fecha_pago", "mes_correspondiente", "monto", "metodo_pago", "comprobante")
    list_filter = ("fecha_pago", "metodo_pago", "concepto")
    search_fields = ("socio__nombre", "socio__apellido", "socio__dni", "comprobante")
    autocomplete_fields = ["socio", "concepto"]