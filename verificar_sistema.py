#!/usr/bin/env python
"""
Script para verificar que el sistema de cuotas está funcionando correctamente
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acftgestion.settings')
django.setup()

from socios.models import Cuota, Concepto, Socio, Pago

def verificar_sistema():
    print("🔍 Verificando Sistema de Gestión de Cuotas")
    print("=" * 50)
    
    # 1. Verificar conceptos
    conceptos_count = Concepto.objects.count()
    print(f"✅ Conceptos registrados: {conceptos_count}")
    
    # 2. Verificar cuotas
    cuotas_count = Cuota.objects.count()
    cuotas_activas = Cuota.objects.filter(activa=True).count()
    print(f"✅ Cuotas totales: {cuotas_count}")
    print(f"✅ Cuotas activas: {cuotas_activas}")
    
    # 3. Verificar pagos
    pagos_count = Pago.objects.count()
    pagos_con_cuota = Pago.objects.filter(cuota__isnull=False).count()
    pagos_antiguos = Pago.objects.filter(cuota__isnull=True).count()
    print(f"✅ Pagos totales: {pagos_count}")
    print(f"✅ Pagos con cuota nueva: {pagos_con_cuota}")
    print(f"✅ Pagos antiguos migrados: {pagos_antiguos}")
    
    # 4. Verificar socios
    socios_count = Socio.objects.count()
    print(f"✅ Socios registrados: {socios_count}")
    
    print("\n📊 Detalle de Cuotas por Año:")
    for cuota in Cuota.objects.order_by('anio', 'mes')[:10]:  # Mostrar las primeras 10
        print(f"   📅 {cuota.codigo}: {cuota} - ${cuota.monto}")
    
    if cuotas_count > 10:
        print(f"   ... y {cuotas_count - 10} cuotas más")
    
    print("\n📊 Últimos Pagos:")
    for pago in Pago.objects.order_by('-fecha_pago')[:5]:  # Últimos 5 pagos
        if pago.cuota:
            print(f"   💰 {pago.socio.nombre} {pago.socio.apellido} - {pago.cuota} - ${pago.monto}")
        else:
            print(f"   💰 {pago.socio.nombre} {pago.socio.apellido} - {pago.mes_correspondiente} (ANTIGUO) - ${pago.monto}")
    
    print("\n🎯 Estado del Sistema:")
    if cuotas_count >= 36:  # 2024, 2025, 2026 = 36 meses
        print("   ✅ Sistema de cuotas configurado correctamente")
    else:
        print("   ⚠️  Faltan cuotas por generar")
    
    if pagos_con_cuota > 0:
        print("   ✅ Sistema de pagos con cuotas funcionando")
    else:
        print("   ⚠️  No hay pagos registrados con el nuevo sistema")
    
    print("\n🚀 ¡Sistema listo para usar!")
    print("   📋 URLs disponibles:")
    print("   • http://127.0.0.1:8000/socios/cuotas/ - Gestión de cuotas")
    print("   • http://127.0.0.1:8000/socios/pagos/ - Lista de pagos")
    print("   • http://127.0.0.1:8000/socios/ - Lista de socios")

if __name__ == "__main__":
    verificar_sistema()
