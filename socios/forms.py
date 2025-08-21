from django import forms
from django.utils import timezone
from .models import Socio, Categoria, Pago, Concepto
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
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
        }

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
            
        # Generar opciones para mes_correspondiente
        # Lista de nombres de meses en español
        nombres_meses = [
            '',  # Para que el índice coincida con el número del mes (enero = 1)
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        
        meses = []
        hoy = timezone.now()
        for i in range(-2, 10):  # Desde 2 meses atrás hasta 9 meses adelante
            fecha = hoy + timezone.timedelta(days=30 * i)
            # Obtener el nombre del mes en español
            nombre_mes = nombres_meses[fecha.month]
            valor = f"{nombre_mes} {fecha.year}"
            meses.append((valor, valor))
        
        self.fields['mes_correspondiente'] = forms.ChoiceField(
            choices=meses,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Filtrar solo conceptos activos
        self.fields['concepto'].queryset = Concepto.objects.filter(activo=True)
        self.fields['concepto'].widget.attrs.update({'class': 'form-select'})
        
    class Meta:
        model = Pago
        fields = [
            'socio',
            'concepto',
            'monto',
            'fecha_pago',
            'mes_correspondiente',
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
