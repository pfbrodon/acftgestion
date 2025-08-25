from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import CategoriaMovimiento, MovimientoCaja, SaldoCaja, TipoMovimiento

@admin.register(CategoriaMovimiento)
class CategoriaMovimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo', 'descripcion']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['tipo', 'nombre']

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'tipo_colored', 'categoria', 'monto_formatted', 
        'descripcion_short', 'pago_relacionado'
    ]
    list_filter = ['tipo', 'categoria', 'fecha']
    search_fields = ['descripcion', 'categoria__nombre']
    date_hierarchy = 'fecha'
    ordering = ['-fecha', '-fecha_creacion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('fecha', 'tipo', 'categoria', 'monto', 'descripcion')
        }),
        ('Relación con Pagos', {
            'fields': ('pago',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_colored(self, obj):
        if obj.tipo == TipoMovimiento.INGRESO:
            return format_html(
                '<span style="color: green; font-weight: bold;">+ {}</span>',
                obj.get_tipo_display()
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">- {}</span>',
                obj.get_tipo_display()
            )
    tipo_colored.short_description = 'Tipo'
    
    def monto_formatted(self, obj):
        if obj.tipo == TipoMovimiento.INGRESO:
            return format_html(
                '<span style="color: green; font-weight: bold;">${}</span>',
                obj.monto
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">${}</span>',
                obj.monto
            )
    monto_formatted.short_description = 'Monto'
    
    def descripcion_short(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_short.short_description = 'Descripción'
    
    def pago_relacionado(self, obj):
        if obj.pago:
            return format_html(
                '<a href="/admin/socios/pago/{}/change/">{}</a>',
                obj.pago.id,
                str(obj.pago)
            )
        return '-'
    pago_relacionado.short_description = 'Pago'

@admin.register(SaldoCaja)
class SaldoCajaAdmin(admin.ModelAdmin):
    list_display = [
        'periodo', 'saldo_inicial_formatted', 'total_ingresos_formatted',
        'total_egresos_formatted', 'saldo_final_formatted', 'fecha_calculo'
    ]
    readonly_fields = [
        'total_ingresos', 'total_egresos', 'saldo_final', 'fecha_calculo'
    ]
    ordering = ['-fecha_fin']
    
    def periodo(self, obj):
        return f"{obj.fecha_inicio} - {obj.fecha_fin}"
    periodo.short_description = 'Período'
    
    def saldo_inicial_formatted(self, obj):
        return format_html('<strong>${}</strong>', obj.saldo_inicial)
    saldo_inicial_formatted.short_description = 'Saldo Inicial'
    
    def total_ingresos_formatted(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">${}</span>',
            obj.total_ingresos
        )
    total_ingresos_formatted.short_description = 'Ingresos'
    
    def total_egresos_formatted(self, obj):
        return format_html(
            '<span style="color: red; font-weight: bold;">${}</span>',
            obj.total_egresos
        )
    total_egresos_formatted.short_description = 'Egresos'
    
    def saldo_final_formatted(self, obj):
        color = 'green' if obj.saldo_final >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 1.1em;">${}</span>',
            color, obj.saldo_final
        )
    saldo_final_formatted.short_description = 'Saldo Final'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calcular_saldo()
        obj.save()
