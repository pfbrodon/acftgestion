from django import forms
from django.utils import timezone
from .models import Socio, Categoria, Pago, Concepto, Cuota
import calendar
import locale

class SocioForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = [
            'nombre',
            'apellido',
            'direccion',
            'dni',
            'categoria',
            'email',
            'celular',
            'fecha_nacimiento',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurarse de que la fecha de nacimiento se muestre en el formato correcto
        if self.instance.pk and self.instance.fecha_nacimiento:
            self.initial['fecha_nacimiento'] = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ConceptoForm(forms.ModelForm):
    class Meta:
        model = Concepto
        fields = ['nombre', 'descripcion', 'monto_sugerido', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'monto_sugerido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        socio = kwargs.pop('socio', None)
        super().__init__(*args, **kwargs)
        
        if socio:
            self.fields['socio'].initial = socio
            self.fields['socio'].widget = forms.HiddenInput()
            
        # Filtrar solo cuotas activas y ordenar por fecha
        self.fields['cuota'].queryset = Cuota.objects.filter(activa=True).order_by('-anio', '-mes')
        self.fields['cuota'].widget.attrs.update({'class': 'form-select', 'id': 'id_cuota'})
        
        # Si estamos editando, no mostrar cuotas ya pagadas por este socio
        if socio and not self.instance.pk:
            cuotas_pagadas = Pago.objects.filter(socio=socio).values_list('cuota_id', flat=True)
            self.fields['cuota'].queryset = self.fields['cuota'].queryset.exclude(id__in=cuotas_pagadas)
        
    class Meta:
        model = Pago
        fields = [
            'socio',
            'cuota',
            'monto',
            'fecha_pago',
            'metodo_pago',
            'comprobante',
            'comentarios'
        ]
        widgets = {
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_monto'}),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'lang': 'es',
                'format': 'dd/mm/yyyy'
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'comprobante': forms.TextInput(attrs={'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Formulario para gestionar cuotas
class CuotaForm(forms.ModelForm):
    class Meta:
        model = Cuota
        fields = ['concepto', 'mes', 'anio', 'monto', 'activa']
        widgets = {
            'concepto': forms.Select(attrs={'class': 'form-select', 'id': 'id_concepto'}),
            'mes': forms.Select(choices=[(i, f"{i:02d}") for i in range(1, 13)], attrs={'class': 'form-select'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'min': 2024, 'max': 2030}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True, 'id': 'id_monto'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo conceptos activos
        self.fields['concepto'].queryset = Concepto.objects.filter(activo=True)
        
        # Si ya hay una instancia con concepto, establecer el monto basado en el concepto
        if self.instance and self.instance.pk:
            try:
                if self.instance.concepto:
                    self.fields['monto'].initial = self.instance.concepto.monto_sugerido
            except Concepto.DoesNotExist:
                pass
