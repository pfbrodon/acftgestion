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
            
        # Generar opciones para mes_correspondiente
        # Lista de nombres de meses en español
        nombres_meses = [
            '',  # Para que el índice coincida con el número del mes (enero = 1)
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        
        meses = []
        # Fecha actual
        hoy = timezone.now()
        
        # Año y mes iniciales (2025-01)
        anio_inicial = 2025
        mes_inicial = 1
        
        # Año y mes actuales
        anio_actual = hoy.year
        mes_actual = hoy.month
        
        # Año y mes finales (2 años después del actual)
        anio_final = anio_actual + 2
        mes_final = mes_actual
        
        # Crear lista de meses desde enero 2025 hasta 2 años después del actual
        for anio in range(anio_inicial, anio_final + 1):
            for mes in range(1, 13):
                # Omitir meses anteriores a enero 2025
                if anio == anio_inicial and mes < mes_inicial:
                    continue
                # Omitir meses posteriores al mes_final en el año_final
                if anio == anio_final and mes > mes_final:
                    continue
                
                nombre_mes = nombres_meses[mes]
                valor = f"{nombre_mes} {anio}"
                meses.append((valor, valor))
        
        # Establecer como valor inicial el mes actual
        valor_mes_actual = f"{nombres_meses[mes_actual]} {anio_actual}"
        
        # Buscar el índice del mes actual en la lista para establecerlo como inicial
        mes_actual_index = next((i for i, (val, _) in enumerate(meses) if val == valor_mes_actual), 0)
        
        self.fields['mes_correspondiente'] = forms.ChoiceField(
            choices=meses,
            initial=meses[mes_actual_index][0] if meses else '',
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
