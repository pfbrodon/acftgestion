from django.core.management.base import BaseCommand
from django.db import transaction
from socios.models import Pago
from caja.models import MovimientoCaja
from decimal import Decimal

class Command(BaseCommand):
    help = 'Corrige los montos de caja para incluir el saldo usado en los pagos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se haría sin realizar cambios',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios')
            )
        
        # Buscar movimientos de caja que tienen pago asociado y donde el monto 
        # del movimiento no coincide con el monto total del pago
        movimientos_a_corregir = []
        
        movimientos = MovimientoCaja.objects.filter(
            pago__isnull=False
        ).select_related('pago')
        
        for movimiento in movimientos:
            pago = movimiento.pago
            monto_saldo_usado = pago.monto_saldo_usado or Decimal('0.00')
            
            # Si el pago usó saldo y el movimiento solo registró el monto efectivo
            if monto_saldo_usado > 0 and movimiento.monto < pago.monto:
                diferencia = pago.monto - movimiento.monto
                movimientos_a_corregir.append({
                    'movimiento': movimiento,
                    'pago': pago,
                    'monto_actual': movimiento.monto,
                    'monto_correcto': pago.monto,
                    'diferencia': diferencia,
                    'saldo_usado': monto_saldo_usado
                })
        
        total_correcciones = len(movimientos_a_corregir)
        
        if total_correcciones == 0:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron movimientos que necesiten corrección')
            )
            return
        
        self.stdout.write(f'Encontrados {total_correcciones} movimientos que necesitan corrección')
        
        # Mostrar detalle de las correcciones
        total_diferencia = Decimal('0.00')
        for item in movimientos_a_corregir:
            mov = item['movimiento']
            pago = item['pago']
            self.stdout.write(
                f"  • Pago #{pago.id} ({pago.socio.nombre} {pago.socio.apellido}) - "
                f"Fecha: {mov.fecha} - "
                f"Actual: ${item['monto_actual']} → Correcto: ${item['monto_correcto']} "
                f"(+${item['diferencia']})"
            )
            total_diferencia += item['diferencia']
        
        self.stdout.write(f'\nTotal de dinero faltante: ${total_diferencia}')
        
        if not dry_run:
            with transaction.atomic():
                correcciones_realizadas = 0
                
                for item in movimientos_a_corregir:
                    movimiento = item['movimiento']
                    pago = item['pago']
                    
                    # Actualizar el monto del movimiento
                    movimiento.monto = pago.monto
                    
                    # Actualizar la descripción para incluir información del saldo usado
                    monto_efectivo = pago.monto - (pago.monto_saldo_usado or Decimal('0.00'))
                    monto_saldo_usado = pago.monto_saldo_usado or Decimal('0.00')
                    
                    if monto_saldo_usado > 0:
                        # Verificar si la descripción ya incluye información de saldo
                        if 'Efectivo:' not in movimiento.descripcion:
                            movimiento.descripcion += f" (Efectivo: ${monto_efectivo}, Saldo usado: ${monto_saldo_usado})"
                    
                    movimiento.save()
                    correcciones_realizadas += 1
                    
                    if correcciones_realizadas % 10 == 0:
                        self.stdout.write(f'Corregidos {correcciones_realizadas}/{total_correcciones} movimientos...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Corrección completada: {correcciones_realizadas} movimientos actualizados'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'💰 Total de dinero agregado al resumen de caja: ${total_diferencia}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Se corregirían {total_correcciones} movimientos, '
                    f'agregando ${total_diferencia} al resumen de caja'
                )
            )