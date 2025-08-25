from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import MovimientoCaja, CategoriaMovimiento, SaldoCaja, TipoMovimiento

class MovimientoCajaListView(ListView):
    model = MovimientoCaja
    template_name = 'caja/movimiento_list.html'
    context_object_name = 'movimientos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MovimientoCaja.objects.select_related('categoria', 'pago__socio')
        
        # Filtros
        tipo = self.request.GET.get('tipo')
        categoria = self.request.GET.get('categoria')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos para filtros
        context['categorias'] = CategoriaMovimiento.objects.filter(activo=True)
        context['tipos'] = TipoMovimiento.choices
        
        # Totales del período filtrado
        queryset = self.get_queryset()
        ingresos = queryset.filter(tipo=TipoMovimiento.INGRESO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        egresos = queryset.filter(tipo=TipoMovimiento.EGRESO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        context['total_ingresos'] = ingresos
        context['total_egresos'] = egresos
        context['balance'] = ingresos - egresos
        
        return context

class MovimientoCajaCreateView(CreateView):
    model = MovimientoCaja
    template_name = 'caja/movimiento_form.html'
    fields = ['fecha', 'tipo', 'categoria', 'monto', 'descripcion']
    success_url = reverse_lazy('caja:movimiento_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Movimiento de Caja'
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Movimiento de caja registrado exitosamente: {form.instance.get_tipo_display()} ${form.instance.monto}'
        )
        return super().form_valid(form)

class MovimientoCajaUpdateView(UpdateView):
    model = MovimientoCaja
    template_name = 'caja/movimiento_form.html'
    fields = ['fecha', 'tipo', 'categoria', 'monto', 'descripcion']
    success_url = reverse_lazy('caja:movimiento_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Movimiento de Caja'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Movimiento de caja actualizado exitosamente')
        return super().form_valid(form)

class MovimientoCajaDeleteView(DeleteView):
    model = MovimientoCaja
    template_name = 'caja/movimiento_confirm_delete.html'
    success_url = reverse_lazy('caja:movimiento_list')
    
    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(request, 'Movimiento de caja eliminado exitosamente')
        return result

def resumen_caja_view(request):
    """Vista del resumen general de caja"""
    
    # Período por defecto: mes actual
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    
    # Obtener fechas del formulario o usar por defecto
    fecha_desde = request.GET.get('fecha_desde', primer_dia_mes)
    fecha_hasta = request.GET.get('fecha_hasta', hoy)
    
    if isinstance(fecha_desde, str):
        fecha_desde = date.fromisoformat(fecha_desde)
    if isinstance(fecha_hasta, str):
        fecha_hasta = date.fromisoformat(fecha_hasta)
    
    # Movimientos del período
    movimientos = MovimientoCaja.objects.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta
    ).select_related('categoria', 'pago__socio')
    
    # Cálculos generales
    total_ingresos = movimientos.filter(tipo=TipoMovimiento.INGRESO).aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    total_egresos = movimientos.filter(tipo=TipoMovimiento.EGRESO).aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    balance = total_ingresos - total_egresos
    
    # Resumen por categorías
    resumen_categorias = []
    categorias = CategoriaMovimiento.objects.filter(activo=True)
    
    for categoria in categorias:
        total_categoria = movimientos.filter(categoria=categoria).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        if total_categoria > 0:
            resumen_categorias.append({
                'categoria': categoria,
                'total': total_categoria,
                'cantidad': movimientos.filter(categoria=categoria).count()
            })
    
    # Últimos movimientos
    ultimos_movimientos = movimientos.order_by('-fecha', '-fecha_creacion')[:10]
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'resumen_categorias': resumen_categorias,
        'ultimos_movimientos': ultimos_movimientos,
        'cantidad_movimientos': movimientos.count(),
    }
    
    return render(request, 'caja/resumen.html', context)
