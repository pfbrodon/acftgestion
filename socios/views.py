from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from .models import Socio, Categoria, Pago, Concepto
from .forms import SocioForm, CategoriaForm, PagoForm, ConceptoForm

# Vistas para Socios
class SocioListView(ListView):
    model = Socio
    template_name = 'socios/socio_list.html'
    context_object_name = 'socios'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calcular estado de pagos para cada socio
        for socio in context['socios']:
            socio.estado = socio.get_estado_pagos()
        return context

class SocioCreateView(CreateView):
    model = Socio
    form_class = SocioForm
    template_name = 'socios/socio_form.html'
    success_url = reverse_lazy('socios:listar')

    def form_valid(self, form):
        messages.success(self.request, "Socio creado exitosamente.")
        return super().form_valid(form)

class SocioUpdateView(UpdateView):
    model = Socio
    form_class = SocioForm
    template_name = 'socios/socio_form.html'
    success_url = reverse_lazy('socios:listar')
    
    def form_valid(self, form):
        messages.success(self.request, "Socio actualizado exitosamente.")
        return super().form_valid(form)

class SocioDeleteView(DeleteView):
    model = Socio
    template_name = 'socios/socio_confirm_delete.html'
    success_url = reverse_lazy('socios:listar')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Socio eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para Categorías
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'socios/categoria_list.html'
    context_object_name = 'categorias'

class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'socios/categoria_form.html'
    success_url = reverse_lazy('socios:listar_categorias')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría creada exitosamente.")
        return super().form_valid(form)

class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'socios/categoria_form.html'
    success_url = reverse_lazy('socios:listar_categorias')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada exitosamente.")
        return super().form_valid(form)

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'socios/categoria_confirm_delete.html'
    success_url = reverse_lazy('socios:listar_categorias')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.object
        return context
    
    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.socios.exists():
            messages.error(request, "No se puede eliminar esta categoría porque tiene socios asociados.")
            return redirect('socios:listar_categorias')
        messages.success(request, "Categoría eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para Pagos
class PagoCreateView(CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'socios/pago_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        socio_id = self.kwargs.get('socio_id')
        if socio_id:
            kwargs['socio'] = get_object_or_404(Socio, pk=socio_id)
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        socio_id = self.kwargs.get('socio_id')
        if socio_id:
            context['socio'] = get_object_or_404(Socio, pk=socio_id)
        return context
    
    def get_success_url(self):
        messages.success(self.request, "Pago registrado exitosamente.")
        socio_id = self.kwargs.get('socio_id') or self.object.socio.id
        return reverse('socios:detalle_socio', kwargs={'pk': socio_id})

class PagoUpdateView(UpdateView):
    model = Pago
    form_class = PagoForm
    template_name = 'socios/pago_form.html'
    
    def get_success_url(self):
        messages.success(self.request, "Pago actualizado exitosamente.")
        return reverse('socios:detalle_socio', kwargs={'pk': self.object.socio.id})

class PagoDeleteView(DeleteView):
    model = Pago
    template_name = 'socios/pago_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, "Pago eliminado exitosamente.")
        return reverse('socios:detalle_socio', kwargs={'pk': self.object.socio.id})

class SocioDetailView(DetailView):
    model = Socio
    template_name = 'socios/socio_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagos'] = self.object.pagos.all().order_by('-fecha_pago')
        context['estado_pagos'] = self.object.get_estado_pagos()
        return context
        
class PagoListView(ListView):
    model = Pago
    template_name = 'socios/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('socio')
        socio_id = self.request.GET.get('socio')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if socio_id:
            queryset = queryset.filter(socio_id=socio_id)
        if fecha_desde:
            queryset = queryset.filter(fecha_pago__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_pago__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_pago')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['socios'] = Socio.objects.all().order_by('apellido', 'nombre')
        
        # Calcular el total de los pagos filtrados
        pagos = self.get_queryset()
        total = sum(pago.monto for pago in pagos)
        context['total_pagos'] = total
        
        return context
        
# Vistas para Conceptos
class ConceptoListView(ListView):
    model = Concepto
    template_name = 'socios/concepto_list.html'
    context_object_name = 'conceptos'

class ConceptoCreateView(CreateView):
    model = Concepto
    form_class = ConceptoForm
    template_name = 'socios/concepto_form.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    
    def form_valid(self, form):
        messages.success(self.request, "Concepto creado exitosamente.")
        return super().form_valid(form)

class ConceptoUpdateView(UpdateView):
    model = Concepto
    form_class = ConceptoForm
    template_name = 'socios/concepto_form.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    
    def form_valid(self, form):
        messages.success(self.request, "Concepto actualizado exitosamente.")
        return super().form_valid(form)

class ConceptoDeleteView(DeleteView):
    model = Concepto
    template_name = 'socios/concepto_confirm_delete.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si el concepto está siendo utilizado en algún pago
        context['pagos_relacionados'] = self.object.pagos.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        concepto = self.get_object()
        if concepto.pagos.exists():
            messages.error(request, "No se puede eliminar este concepto porque tiene pagos asociados.")
            return redirect('socios:listar_conceptos')
        messages.success(request, "Concepto eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)
        
# Vista para obtener el monto sugerido de un concepto
def get_concepto_monto(request):
    concepto_id = request.GET.get('concepto_id')
    try:
        concepto = Concepto.objects.get(pk=concepto_id)
        return JsonResponse({'monto_sugerido': float(concepto.monto_sugerido)})
    except (Concepto.DoesNotExist, ValueError):
        return JsonResponse({'monto_sugerido': 0})