from django.core.management.base import BaseCommand
from django.db import models
from socios.models import Pago
from caja.models import MovimientoCaja
from decimal import Decimal

class Command(BaseCommand):
    help = 'Investiga el estado de los pagos con saldo usado y sus movimientos de caja'
    
    def handle(self, *args, **options):
        # Buscar pagos que hayan usado saldo
        pagos_con_saldo = Pago.objects.filter(
            monto_saldo_usado__gt=Decimal('0')
        ).select_related('socio')
        
        self.stdout.write(f"=== PAGOS CON SALDO USADO ({pagos_con_saldo.count()}) ===")
        
        total_diferencia = Decimal('0.00')
        
        for pago in pagos_con_saldo:
            monto_efectivo = pago.monto - (pago.monto_saldo_usado or Decimal('0'))
            
            self.stdout.write(
                f"Pago #{pago.id}: {pago.socio.nombre} {pago.socio.apellido}\n"
                f"  - Monto total: ${pago.monto}\n"
                f"  - Saldo usado: ${pago.monto_saldo_usado}\n"
                f"  - Efectivo: ${monto_efectivo}"
            )
            
            # Buscar movimiento de caja asociado
            try:
                movimiento = MovimientoCaja.objects.get(pago=pago)
                diferencia = pago.monto - movimiento.monto
                
                self.stdout.write(
                    f"  - Movimiento de caja: ${movimiento.monto}\n"
                    f"  - Diferencia: ${diferencia}"
                )
                
                if diferencia > 0:
                    total_diferencia += diferencia
                    
            except MovimientoCaja.DoesNotExist:
                self.stdout.write("  - NO tiene movimiento de caja asociado")
            
            self.stdout.write("-" * 50)
        
        # Verificar también pagos sin movimiento de caja
        pagos_sin_movimiento = Pago.objects.filter(
            movimientocaja__isnull=True
        ).count()
        
        self.stdout.write(f"\n=== RESUMEN ===")
        self.stdout.write(f"Pagos con saldo usado: {pagos_con_saldo.count()}")
        self.stdout.write(f"Pagos sin movimiento de caja: {pagos_sin_movimiento}")
        self.stdout.write(f"Total dinero faltante en caja: ${total_diferencia}")
        
        # Mostrar totales actuales de caja
        total_movimientos = MovimientoCaja.objects.filter(
            tipo='ingreso'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_pagos = Pago.objects.aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        self.stdout.write(f"\n=== COMPARACIÓN TOTALES ===")
        self.stdout.write(f"Total en movimientos de caja (ingresos): ${total_movimientos}")
        self.stdout.write(f"Total en pagos registrados: ${total_pagos}")
        self.stdout.write(f"Diferencia: ${total_pagos - total_movimientos}")