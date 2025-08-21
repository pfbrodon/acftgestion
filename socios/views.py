from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Socio
from .forms import SocioForm

class SocioListView(ListView):
	model = Socio
	template_name = 'socios/socio_list.html'
	context_object_name = 'socios'

class SocioCreateView(CreateView):
	model = Socio
	form_class = SocioForm
	template_name = 'socios/socio_form.html'
	success_url = reverse_lazy('socios:listar')

class SocioUpdateView(UpdateView):
	model = Socio
	form_class = SocioForm
	template_name = 'socios/socio_form.html'
	success_url = reverse_lazy('socios:listar')

class SocioDeleteView(DeleteView):
	model = Socio
	template_name = 'socios/socio_confirm_delete.html'
	success_url = reverse_lazy('socios:listar')
