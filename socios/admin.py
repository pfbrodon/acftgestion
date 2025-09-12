from django.contrib import admin
from .models import Socio, Categoria, Pago, Concepto, Cuota, SaldoSocio, DetallePago, MovimientoSaldo

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

class DetallePagoInline(admin.TabularInline):
    model = DetallePago
    extra = 0
    fields = ('cuota', 'monto_aplicado', 'monto_restante', 'pagado_completamente')
    readonly_fields = ('monto_restante', 'pagado_completamente')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("socio", "get_cuotas_display", "fecha_pago", "monto", "es_pago_multiple", "metodo_pago", "comprobante")
    list_filter = ("fecha_pago", "metodo_pago", "es_pago_multiple")
    search_fields = ("socio__nombre", "socio__apellido", "socio__dni", "comprobante")
    inlines = [DetallePagoInline]
    
    def get_cuotas_display(self, obj):
        if obj.es_pago_multiple:
            return f"Múltiple ({obj.detalles.count()} cuotas)"
        elif obj.cuota:
            return str(obj.cuota)
        else:
            return "N/A"
    get_cuotas_display.short_description = "Cuotas"

class MovimientoSaldoInline(admin.TabularInline):
    model = MovimientoSaldo
    extra = 0
    fields = ('fecha', 'monto', 'saldo_anterior', 'saldo_nuevo', 'descripcion')
    readonly_fields = ('fecha', 'saldo_anterior', 'saldo_nuevo')

@admin.register(SaldoSocio)
class SaldoSocioAdmin(admin.ModelAdmin):
    list_display = ("socio", "saldo_actual", "fecha_actualizacion")
    search_fields = ("socio__nombre", "socio__apellido", "socio__dni")
    readonly_fields = ("fecha_actualizacion",)
    inlines = [MovimientoSaldoInline]

@admin.register(DetallePago)
class DetallePagoAdmin(admin.ModelAdmin):
    list_display = ("pago", "cuota", "monto_aplicado", "monto_restante", "pagado_completamente")
    list_filter = ("pagado_completamente", "cuota__concepto")
    search_fields = ("pago__socio__nombre", "pago__socio__apellido", "cuota__codigo")

@admin.register(MovimientoSaldo)
class MovimientoSaldoAdmin(admin.ModelAdmin):
    list_display = ("saldo_socio", "fecha", "monto", "saldo_nuevo", "descripcion")
    list_filter = ("fecha",)
    search_fields = ("saldo_socio__socio__nombre", "saldo_socio__socio__apellido", "descripcion")
    readonly_fields = ("fecha", "saldo_anterior", "saldo_nuevo")