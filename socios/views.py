from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView, TemplateView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from .models import Socio, Categoria, Pago, Concepto
from .forms import SocioForm, CategoriaForm, PagoForm, ConceptoForm
from .auth_forms import RegistroUsuarioForm, LoginForm

# Clase base para verificar si un usuario es administrador
class EsAdministradorMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, 'socio'):
            return self.request.user.socio.es_administrador
        return False
    
    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para realizar esta acción. Solo los administradores pueden acceder.")
        if self.request.user.is_authenticated and hasattr(self.request.user, 'socio'):
            return redirect('socios:mi_perfil')
        return redirect('socios:login')

# Vistas para Socios
class SocioListView(LoginRequiredMixin, EsAdministradorMixin, ListView):
    model = Socio
    template_name = 'socios/socio_list.html'
    context_object_name = 'socios'
    login_url = 'socios:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calcular estado de pagos para cada socio
        for socio in context['socios']:
            socio.estado = socio.get_estado_pagos()
        return context

class SocioCreateView(LoginRequiredMixin, EsAdministradorMixin, CreateView):
    model = Socio
    form_class = SocioForm
    template_name = 'socios/socio_form.html'
    success_url = reverse_lazy('socios:listar')
    login_url = 'socios:login'

    def form_valid(self, form):
        messages.success(self.request, "Socio creado exitosamente.")
        return super().form_valid(form)

class SocioUpdateView(LoginRequiredMixin, EsAdministradorMixin, UpdateView):
    model = Socio
    form_class = SocioForm
    template_name = 'socios/socio_form.html'
    success_url = reverse_lazy('socios:listar')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Socio actualizado exitosamente.")
        return super().form_valid(form)

class SocioDeleteView(LoginRequiredMixin, EsAdministradorMixin, DeleteView):
    model = Socio
    template_name = 'socios/socio_confirm_delete.html'
    success_url = reverse_lazy('socios:listar')
    login_url = 'socios:login'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Socio eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para Categorías
class CategoriaListView(LoginRequiredMixin, EsAdministradorMixin, ListView):
    model = Categoria
    template_name = 'socios/categoria_list.html'
    context_object_name = 'categorias'
    login_url = 'socios:login'

class CategoriaCreateView(LoginRequiredMixin, EsAdministradorMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'socios/categoria_form.html'
    success_url = reverse_lazy('socios:listar_categorias')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría creada exitosamente.")
        return super().form_valid(form)

class CategoriaUpdateView(LoginRequiredMixin, EsAdministradorMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'socios/categoria_form.html'
    success_url = reverse_lazy('socios:listar_categorias')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada exitosamente.")
        return super().form_valid(form)

class CategoriaDeleteView(LoginRequiredMixin, EsAdministradorMixin, DeleteView):
    model = Categoria
    template_name = 'socios/categoria_confirm_delete.html'
    success_url = reverse_lazy('socios:listar_categorias')
    login_url = 'socios:login'
    
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
class PagoCreateView(LoginRequiredMixin, EsAdministradorMixin, CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'socios/pago_form.html'
    login_url = 'socios:login'
    
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

class PagoUpdateView(LoginRequiredMixin, EsAdministradorMixin, UpdateView):
    model = Pago
    form_class = PagoForm
    template_name = 'socios/pago_form.html'
    login_url = 'socios:login'
    
    def get_success_url(self):
        messages.success(self.request, "Pago actualizado exitosamente.")
        return reverse('socios:detalle_socio', kwargs={'pk': self.object.socio.id})

class PagoDeleteView(LoginRequiredMixin, EsAdministradorMixin, DeleteView):
    model = Pago
    template_name = 'socios/pago_confirm_delete.html'
    login_url = 'socios:login'
    
    def get_success_url(self):
        messages.success(self.request, "Pago eliminado exitosamente.")
        return reverse('socios:detalle_socio', kwargs={'pk': self.object.socio.id})

class SocioDetailView(LoginRequiredMixin, DetailView):
    model = Socio
    template_name = 'socios/socio_detail.html'
    login_url = 'socios:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagos'] = self.object.pagos.all().order_by('-fecha_pago')
        context['estado_pagos'] = self.object.get_estado_pagos()
        context['es_admin'] = self.request.user.is_superuser or (hasattr(self.request.user, 'socio') and self.request.user.socio.es_administrador)
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # Solo permitir ver el detalle si es el propio socio o un administrador
        socio = self.get_object()
        if (hasattr(request.user, 'socio') and request.user.socio.id == socio.id) or \
           request.user.is_superuser or \
           (hasattr(request.user, 'socio') and request.user.socio.es_administrador):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "No tienes permiso para ver el detalle de este socio.")
            return redirect('socios:mi_perfil')
        
class PagoListView(LoginRequiredMixin, EsAdministradorMixin, ListView):
    model = Pago
    template_name = 'socios/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 10
    login_url = 'socios:login'
    
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
class ConceptoListView(LoginRequiredMixin, EsAdministradorMixin, ListView):
    model = Concepto
    template_name = 'socios/concepto_list.html'
    context_object_name = 'conceptos'
    login_url = 'socios:login'

class ConceptoCreateView(LoginRequiredMixin, EsAdministradorMixin, CreateView):
    model = Concepto
    form_class = ConceptoForm
    template_name = 'socios/concepto_form.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Concepto creado exitosamente.")
        return super().form_valid(form)

class ConceptoUpdateView(LoginRequiredMixin, EsAdministradorMixin, UpdateView):
    model = Concepto
    form_class = ConceptoForm
    template_name = 'socios/concepto_form.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Concepto actualizado exitosamente.")
        return super().form_valid(form)

class ConceptoDeleteView(LoginRequiredMixin, EsAdministradorMixin, DeleteView):
    model = Concepto
    template_name = 'socios/concepto_confirm_delete.html'
    success_url = reverse_lazy('socios:listar_conceptos')
    login_url = 'socios:login'
    
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
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
        
    # Verificar si es administrador
    es_admin = request.user.is_superuser or (hasattr(request.user, 'socio') and request.user.socio.es_administrador)
    if not es_admin:
        return JsonResponse({'error': 'No tienes permisos suficientes'}, status=403)
    
    concepto_id = request.GET.get('concepto_id')
    try:
        concepto = Concepto.objects.get(pk=concepto_id)
        return JsonResponse({'monto_sugerido': float(concepto.monto_sugerido)})
    except (Concepto.DoesNotExist, ValueError):
        return JsonResponse({'monto_sugerido': 0})
        
# Vistas para autenticación
class SocioLoginView(LoginView):
    form_class = LoginForm
    template_name = 'socios/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser or hasattr(self.request.user, 'socio') and self.request.user.socio.es_administrador:
            return reverse('socios:listar')
        elif hasattr(self.request.user, 'socio'):
            return reverse('socios:mi_perfil')
        else:
            return reverse('socios:login')

class SocioLogoutView(LogoutView):
    next_page = 'socios:login'
    # Permitir solicitudes GET para cerrar sesión
    http_method_names = ['get', 'post', 'options']

class RegistroView(FormView):
    template_name = 'socios/registro.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('socios:login')
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "¡Registro exitoso! Tu categoría inicial es 'Cadete'. Un administrador revisará tu información.")
        return super().form_valid(form)

class MiPerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'socios/mi_perfil.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'socio'):
            socio = self.request.user.socio
            context['socio'] = socio
            context['pagos'] = socio.pagos.all().order_by('-fecha_pago')
            context['estado_pagos'] = socio.get_estado_pagos()
            context['es_admin'] = socio.es_administrador or self.request.user.is_superuser
        return context