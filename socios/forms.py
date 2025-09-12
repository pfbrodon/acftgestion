from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from .models import Socio, Categoria, Pago, Concepto, Cuota, SaldoSocio, DetallePago
import calendar
import locale
from decimal import Decimal

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

class PagoMultipleForm(forms.ModelForm):
    """Formulario para pagos múltiples con manejo de saldos"""
    
    cuotas_seleccionadas = forms.ModelMultipleChoiceField(
        queryset=Cuota.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Seleccionar cuotas a pagar"
    )
    
    usar_saldo_disponible = forms.BooleanField(
        required=False,
        label="Usar saldo a favor disponible",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        self.socio = kwargs.pop('socio', None)
        super().__init__(*args, **kwargs)
        
        if self.socio:
            self.fields['socio'].initial = self.socio
            self.fields['socio'].widget = forms.HiddenInput()
            
            # Obtener cuotas disponibles para pagar
            cuotas_disponibles = self.get_cuotas_disponibles()
            self.fields['cuotas_seleccionadas'].queryset = cuotas_disponibles
            
            # Mostrar saldo actual del socio
            try:
                saldo_socio = SaldoSocio.objects.get(socio=self.socio)
                saldo_actual = saldo_socio.saldo_actual
            except SaldoSocio.DoesNotExist:
                saldo_actual = Decimal('0.00')
            
            if saldo_actual > 0:
                self.fields['usar_saldo_disponible'].help_text = f"Saldo disponible: ${saldo_actual}"
                # Agregar método "Saldo a favor" a las opciones cuando hay saldo disponible
                metodo_choices = list(self.fields['metodo_pago'].widget.choices)
                if not any(choice[0] == 'saldo_favor' for choice in metodo_choices):
                    metodo_choices.append(('saldo_favor', 'Saldo a favor'))
                    self.fields['metodo_pago'].widget.choices = metodo_choices
            else:
                self.fields['usar_saldo_disponible'].widget = forms.HiddenInput()
                self.fields['usar_saldo_disponible'].initial = False
                # Remover método "Saldo a favor" si no hay saldo disponible
                metodo_choices = [choice for choice in self.fields['metodo_pago'].widget.choices 
                                if choice[0] != 'saldo_favor']
                self.fields['metodo_pago'].widget.choices = metodo_choices
        
        # Configurar el campo es_pago_multiple como oculto
        self.fields['es_pago_multiple'].initial = True
        self.fields['es_pago_multiple'].widget = forms.HiddenInput()
        
        # Quitar el campo cuota individual ya que usamos selección múltiple
        if 'cuota' in self.fields:
            del self.fields['cuota']
    
    def get_cuotas_disponibles(self):
        """Obtiene las cuotas que el socio puede pagar"""
        if not self.socio:
            return Cuota.objects.none()
        
        # Cuotas activas
        cuotas_activas = Cuota.objects.filter(activa=True).order_by('-anio', '-mes')
        
        # Excluir cuotas ya pagadas completamente
        cuotas_pagadas_completas = []
        for cuota in cuotas_activas:
            total_pagado = DetallePago.objects.filter(
                cuota=cuota,
                pago__socio=self.socio
            ).aggregate(
                total=models.Sum('monto_aplicado')
            )['total'] or Decimal('0.00')
            
            if total_pagado >= cuota.monto:
                cuotas_pagadas_completas.append(cuota.id)
        
        return cuotas_activas.exclude(id__in=cuotas_pagadas_completas)
    
    def clean(self):
        cleaned_data = super().clean()
        cuotas_seleccionadas = cleaned_data.get('cuotas_seleccionadas')
        monto = cleaned_data.get('monto')
        usar_saldo = cleaned_data.get('usar_saldo_disponible', False)
        
        if cuotas_seleccionadas and monto is not None:
            # Calcular monto total de las cuotas seleccionadas
            monto_total_cuotas = sum(cuota.monto for cuota in cuotas_seleccionadas)
            
            # Obtener saldo disponible
            saldo_disponible = Decimal('0.00')
            if self.socio and usar_saldo:
                try:
                    saldo_socio = SaldoSocio.objects.get(socio=self.socio)
                    saldo_disponible = max(saldo_socio.saldo_actual, Decimal('0.00'))
                except SaldoSocio.DoesNotExist:
                    saldo_disponible = Decimal('0.00')
            
            # Validar que el monto + saldo sea suficiente o genere un saldo válido
            monto_total_disponible = monto + saldo_disponible
            
            if monto_total_disponible < 0:
                raise ValidationError("El monto no puede ser negativo.")
            
            # Validar que si el monto es 0, al menos se esté usando saldo disponible
            if monto <= 0 and not usar_saldo:
                raise ValidationError("Debes ingresar un monto mayor a 0 o usar tu saldo disponible.")
            
            # Validar que el monto total disponible cubra algo
            if monto_total_disponible <= 0:
                raise ValidationError("Debes ingresar un monto o tener saldo disponible para pagar.")
            
            # Información para el usuario
            if monto_total_disponible < monto_total_cuotas:
                diferencia = monto_total_cuotas - monto_total_disponible
                cleaned_data['_info_faltante'] = diferencia
            elif monto_total_disponible > monto_total_cuotas:
                sobrante = monto_total_disponible - monto_total_cuotas
                cleaned_data['_info_sobrante'] = sobrante
            
            cleaned_data['_monto_total_cuotas'] = monto_total_cuotas
            cleaned_data['_saldo_disponible'] = saldo_disponible
        
        return cleaned_data
    
    class Meta:
        model = Pago
        fields = [
            'socio',
            'es_pago_multiple',
            'monto',
            'fecha_pago',
            'metodo_pago',
            'comprobante',
            'comentarios'
        ]
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'id': 'id_monto_multiple',
                'min': '0'
            }),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'lang': 'es'
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'comprobante': forms.TextInput(attrs={'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
