from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView, TemplateView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.db.models import ProtectedError
from .models import Socio, Categoria, Pago, Concepto, Cuota
from .forms import SocioForm, CategoriaForm, PagoForm, ConceptoForm, CuotaForm
from .auth_forms import RegistroUsuarioForm, LoginForm

# Imports para PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import black, blue, grey
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

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
    paginate_by = 24  # Aumentar a 24 como en otras listas
    login_url = 'socios:login'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('socio', 'concepto', 'cuota')
        socio_id = self.request.GET.get('socio')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if socio_id:
            queryset = queryset.filter(socio_id=socio_id)
        if fecha_desde:
            queryset = queryset.filter(fecha_pago__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_pago__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_pago', '-id')
    
    def get_context_data(self, **kwargs):
        from datetime import date
        
        context = super().get_context_data(**kwargs)
        context['socios'] = Socio.objects.all().order_by('apellido', 'nombre')
        
        # Calcular el total de los pagos filtrados
        pagos = self.get_queryset()
        total = sum(pago.monto for pago in pagos)
        context['total_pagos'] = total
        
        # Calcular promedio
        cantidad_pagos = pagos.count()
        if cantidad_pagos > 0:
            context['promedio_pagos'] = total / cantidad_pagos
        else:
            context['promedio_pagos'] = 0
        
        # Calcular pagos del mes actual
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        pagos_mes_actual = Pago.objects.filter(
            fecha_pago__gte=primer_dia_mes,
            fecha_pago__lte=hoy
        ).count()
        context['pagos_mes_actual'] = pagos_mes_actual
        
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
        # Verificar si el concepto está siendo utilizado en alguna cuota
        context['cuotas_relacionadas'] = self.object.cuotas.count()
        # También verificar pagos antiguos que podrían estar relacionados
        context['pagos_antiguos'] = getattr(self.object, 'pagos_antiguos', []).count() if hasattr(self.object, 'pagos_antiguos') else 0
        return context
    
    def delete(self, request, *args, **kwargs):
        concepto = self.get_object()
        try:
            # Verificar si tiene cuotas asociadas
            if concepto.cuotas.exists():
                messages.error(request, "No se puede eliminar este concepto porque tiene cuotas asociadas.")
                return redirect('socios:listar_conceptos')
            # Verificar si tiene pagos antiguos
            if hasattr(concepto, 'pagos_antiguos') and concepto.pagos_antiguos.exists():
                messages.error(request, "No se puede eliminar este concepto porque tiene pagos antiguos asociados.")
                return redirect('socios:listar_conceptos')
            
            messages.success(request, "Concepto eliminado exitosamente.")
            return super().delete(request, *args, **kwargs)
            
        except ProtectedError as e:
            # Capturar error de relaciones protegidas
            cuotas_count = concepto.cuotas.count()
            pagos_count = getattr(concepto, 'pagos_antiguos', []).count() if hasattr(concepto, 'pagos_antiguos') else 0
            
            if cuotas_count > 0:
                messages.error(
                    request, 
                    f"No se puede eliminar este concepto porque tiene {cuotas_count} cuota(s) asociada(s). "
                    f"Elimine o cambie todas las cuotas relacionadas primero."
                )
            elif pagos_count > 0:
                messages.error(
                    request, 
                    f"No se puede eliminar este concepto porque tiene {pagos_count} pago(s) asociado(s)."
                )
            else:
                messages.error(
                    request, 
                    "No se puede eliminar este concepto porque tiene elementos relacionados."
                )
            return redirect('socios:listar_conceptos')
        
# Vista para obtener el monto de una cuota
def get_cuota_monto(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
        
    # Verificar si es administrador
    es_admin = request.user.is_superuser or (hasattr(request.user, 'socio') and request.user.socio.es_administrador)
    if not es_admin:
        return JsonResponse({'error': 'No tienes permisos suficientes'}, status=403)
    
    cuota_id = request.GET.get('cuota_id')
    try:
        cuota = Cuota.objects.get(pk=cuota_id)
        return JsonResponse({'monto': float(cuota.monto)})
    except (Cuota.DoesNotExist, ValueError):
        return JsonResponse({'monto': 0})

# Vista para obtener el monto de un concepto
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
        return JsonResponse({'monto': float(concepto.monto_sugerido)})
    except (Concepto.DoesNotExist, ValueError):
        return JsonResponse({'monto': 0})
        
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

# Vistas para Cuotas
class CuotaListView(LoginRequiredMixin, EsAdministradorMixin, ListView):
    model = Cuota
    template_name = 'socios/cuota_list.html'
    context_object_name = 'cuotas'
    paginate_by = 24  # Mostrar más cuotas por página
    login_url = 'socios:login'
    
    def get_queryset(self):
        queryset = Cuota.objects.all().order_by('-anio', '-mes')
        
        # Filtrar por año si se especifica
        anio = self.request.GET.get('anio')
        if anio:
            try:
                queryset = queryset.filter(anio=int(anio))
            except ValueError:
                pass  # Ignorar valores inválidos
        
        # Filtrar por estado si se especifica
        activa = self.request.GET.get('activa')
        if activa in ['True', 'False']:
            queryset = queryset.filter(activa=activa == 'True')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_cuotas'] = Cuota.objects.count()
        context['cuotas_activas'] = Cuota.objects.filter(activa=True).count()
        context['cuotas_inactivas'] = Cuota.objects.filter(activa=False).count()
        
        # Agregar años disponibles para el filtro
        context['anios_disponibles'] = Cuota.objects.values_list('anio', flat=True).distinct().order_by('-anio')
        context['anio_seleccionado'] = self.request.GET.get('anio', '')
        context['estado_seleccionado'] = self.request.GET.get('activa', '')
        
        return context

class CuotaCreateView(LoginRequiredMixin, EsAdministradorMixin, CreateView):
    model = Cuota
    form_class = CuotaForm
    template_name = 'socios/cuota_form.html'
    success_url = reverse_lazy('socios:listar_cuotas')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Cuota creada exitosamente.")
        return super().form_valid(form)

class CuotaUpdateView(LoginRequiredMixin, EsAdministradorMixin, UpdateView):
    model = Cuota
    form_class = CuotaForm
    template_name = 'socios/cuota_form.html'
    success_url = reverse_lazy('socios:listar_cuotas')
    login_url = 'socios:login'
    
    def form_valid(self, form):
        messages.success(self.request, "Cuota actualizada exitosamente.")
        return super().form_valid(form)

class CuotaDeleteView(LoginRequiredMixin, EsAdministradorMixin, DeleteView):
    model = Cuota
    template_name = 'socios/cuota_confirm_delete.html'
    success_url = reverse_lazy('socios:listar_cuotas')
    login_url = 'socios:login'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cuota eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vista para generar PDF del recibo de pago
def generar_recibo_pdf(request, pago_id):
    """Genera un PDF con el recibo de pago"""
    pago = get_object_or_404(Pago, id=pago_id)
    
    # Verificar permisos
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Acceso denegado")
    
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'socio') and request.user.socio.es_administrador) or
            (hasattr(request.user, 'socio') and request.user.socio == pago.socio)):
        return HttpResponseForbidden("No tiene permisos para ver este recibo")
    
    # Crear el PDF con la mitad del tamaño A4 y márgenes mínimos
    buffer = BytesIO()
    # A4 es 210x297mm, la mitad sería 210x148.5mm (aproximadamente 595x420 puntos)
    page_width = 595  # Ancho A4 completo
    page_height = 420  # Mitad de la altura A4
    doc = SimpleDocTemplate(buffer, pagesize=(page_width, page_height), 
                          rightMargin=1*cm, leftMargin=1*cm,
                          topMargin=1*cm, bottomMargin=1*cm)
    
    # Estilos ultra compactos para una sola página
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=blue
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=9,
        spaceAfter=4,
        alignment=TA_LEFT,
        textColor=black
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=2,
        alignment=TA_LEFT
    )
    
    # Contenido del PDF
    story = []
    
    # Título
    title = Paragraph("RECIBO DE PAGO", title_style)
    story.append(title)
    story.append(Spacer(1, 4))
    
    # Información del club y número de recibo en la misma línea
    fecha_actual = datetime.now()
    numero_recibo = f"REC-{pago.id:06d}"
    club_info = Paragraph(f"<b>Club de Ferromodelismo</b> - Recibo N°: {numero_recibo} - {fecha_actual.strftime('%d/%m/%Y')}", normal_style)
    story.append(club_info)
    story.append(Spacer(1, 6))
    
    # Información del socio
    socio_header = Paragraph("DATOS DEL SOCIO", header_style)
    story.append(socio_header)
    
    # Tabla con datos del socio
    socio_data = [
        ['Nombre completo:', f"{pago.socio.nombre} {pago.socio.apellido}"],
        ['DNI:', pago.socio.dni or 'No especificado'],
        ['Categoría:', str(pago.socio.categoria)],
        ['Email:', pago.socio.email or 'No especificado'],
        ['Teléfono:', pago.socio.celular or 'No especificado'],
    ]
    
    socio_table = Table(socio_data, colWidths=[2.2*cm, 9.3*cm])
    socio_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(socio_table)
    story.append(Spacer(1, 6))
    
    # Información del pago
    pago_header = Paragraph("DETALLE DEL PAGO", header_style)
    story.append(pago_header)
    
    # Determinar concepto
    if pago.cuota:
        concepto_pago = f"Cuota {pago.cuota}"
        periodo = f"Período: {pago.cuota}"
    else:
        concepto_pago = pago.concepto.nombre if pago.concepto else "No especificado"
        if pago.mes_correspondiente and pago.año_correspondiente:
            periodo = f"Período: {pago.mes_correspondiente}/{pago.año_correspondiente}"
        else:
            periodo = "Período: No especificado"
    
    # Tabla con datos del pago
    pago_data = [
        ['Concepto:', concepto_pago],
        ['', periodo],
        ['Fecha de pago:', pago.fecha_pago.strftime('%d/%m/%Y')],
        ['Método de pago:', pago.get_metodo_pago_display()],
        ['Comprobante:', pago.comprobante or 'No especificado'],
        ['Monto pagado:', f"$ {pago.monto:,.2f}"],
    ]
    
    pago_table = Table(pago_data, colWidths=[2.2*cm, 9.3*cm])
    pago_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        # Resaltar la fila del monto
        ('BACKGROUND', (0, -1), (-1, -1), grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),
    ]))
    
    story.append(pago_table)
    story.append(Spacer(1, 6))
    
    # Comentarios si existen (más compactos)
    if pago.comentarios:
        comentarios_text = Paragraph(f"<b>Observaciones:</b> {pago.comentarios}", normal_style)
        story.append(comentarios_text)
        story.append(Spacer(1, 4))
    
    # Pie de página ultra compacto
    pie_style = ParagraphStyle(
        'Pie',
        parent=styles['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=grey
    )
    
    story.append(Spacer(1, 6))
    pie = Paragraph("Este documento certifica el pago realizado - Club de Ferromodelismo", pie_style)
    story.append(pie)
    
    # Generar el PDF
    doc.build(story)
    
    # Configurar la respuesta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"recibo_pago_{numero_recibo}_{pago.socio.apellido}_{pago.socio.nombre}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response