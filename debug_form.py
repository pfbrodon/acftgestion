#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acftgestion.settings')
django.setup()

from socios.models import Socio, Cuota
from socios.forms import PagoMultipleForm

# Verificar datos
print("=== Debug del PagoMultipleForm ===")
print(f"Total cuotas en DB: {Cuota.objects.count()}")
print(f"Total socios en DB: {Socio.objects.count()}")

# Verificar si existe el socio 3
try:
    socio = Socio.objects.get(pk=3)
    print(f"Socio encontrado: {socio}")
    
    # Crear el formulario
    form = PagoMultipleForm(socio=socio)
    
    # Obtener cuotas disponibles
    cuotas_disponibles = form.get_cuotas_disponibles()
    print(f"Cuotas disponibles para {socio}: {cuotas_disponibles.count()}")
    
    for cuota in cuotas_disponibles[:5]:
        print(f"- {cuota} (ID: {cuota.id}, Monto: ${cuota.monto})")
        
    # Verificar el queryset del campo
    print(f"Queryset del campo cuotas_seleccionadas: {form.fields['cuotas_seleccionadas'].queryset.count()}")
    
except Socio.DoesNotExist:
    print("El socio con ID 3 no existe")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
