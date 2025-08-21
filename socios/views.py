from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.shortcuts import redirect
from .models import Socio, Categoria
from .forms import SocioForm, CategoriaForm

# Vistas para Socios
class SocioListView(ListView):
    model = Socio
    template_name = 'socios/socio_list.html'
    context_object_name = 'socios'

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