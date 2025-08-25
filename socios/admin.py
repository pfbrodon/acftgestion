from django.contrib import admin
from .models import Socio, Categoria, Pago, Concepto, Cuota

@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "monto_sugerido", "activo", "descripcion")
    search_fields = ("nombre",)
    list_filter = ("activo",)

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "get_periodo", "concepto", "monto", "activa", "fecha_creacion")
    search_fields = ("codigo", "concepto__nombre")
    list_filter = ("anio", "mes", "concepto", "activa")
    ordering = ["-anio", "-mes"]
    
    def get_periodo(self, obj):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[obj.mes]} {obj.anio}"
    get_periodo.short_description = "Período"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    fields = ('cuota', 'fecha_pago', 'monto', 'metodo_pago', 'comprobante')
    autocomplete_fields = ['cuota']

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
    list_display = ("socio", "cuota", "fecha_pago", "monto", "metodo_pago", "comprobante")
    list_filter = ("fecha_pago", "metodo_pago", "cuota__concepto")
    search_fields = ("socio__nombre", "socio__apellido", "socio__dni", "comprobante", "cuota__codigo")
    autocomplete_fields = ["socio", "cuota"]