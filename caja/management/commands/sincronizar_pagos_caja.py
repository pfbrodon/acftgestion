from django.core.management.base import BaseCommand
from django.db import transaction
from socios.models import Pago
from caja.models import MovimientoCaja, CategoriaMovimiento, TipoMovimiento

class Command(BaseCommand):
    help = 'Sincroniza los pagos existentes con movimientos de caja'
    
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
        
        # Buscar o crear la categoría para ingresos por cuotas
        if not dry_run:
            categoria_cuotas, created = CategoriaMovimiento.objects.get_or_create(
                nombre="Cuotas Sociales",
                defaults={
                    'tipo': TipoMovimiento.INGRESO,
                    'descripcion': "Ingresos por pagos de cuotas de socios",
                    'activo': True
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Categoría "Cuotas Sociales" creada')
                )
        else:
            categoria_cuotas = None
        
        # Obtener pagos que no tienen movimiento de caja asociado
        pagos_sin_movimiento = Pago.objects.filter(
            movimientocaja__isnull=True
        ).select_related('socio', 'concepto', 'cuota')
        
        total_pagos = pagos_sin_movimiento.count()
        
        if total_pagos == 0:
            self.stdout.write(
                self.style.SUCCESS('Todos los pagos ya tienen movimientos de caja asociados')
            )
            return
        
        self.stdout.write(f'Encontrados {total_pagos} pagos sin movimiento de caja')
        
        movimientos_creados = 0
        
        with transaction.atomic():
            for pago in pagos_sin_movimiento:
                # Crear descripción detallada
                if pago.es_pago_multiple:
                    descripcion = f"Pago múltiple - {pago.socio.nombre} {pago.socio.apellido}"
                elif pago.cuota:
                    descripcion = f"Pago de cuota {pago.cuota} - {pago.socio.nombre} {pago.socio.apellido}"
                elif pago.concepto:
                    # Para pagos antiguos (sistema de conceptos)
                    descripcion = f"Pago de {pago.concepto.nombre} - {pago.socio.nombre} {pago.socio.apellido}"
                    if hasattr(pago, 'mes_correspondiente') and pago.mes_correspondiente and pago.año_correspondiente:
                        descripcion += f" ({pago.mes_correspondiente}/{pago.año_correspondiente})"
                else:
                    # Fallback para casos inesperados
                    descripcion = f"Pago - {pago.socio.nombre} {pago.socio.apellido}"
                
                if not dry_run:
                    # Mejorar descripción si se usó saldo
                    monto_saldo_usado = pago.monto_saldo_usado or 0
                    if monto_saldo_usado > 0:
                        monto_efectivo = pago.monto - monto_saldo_usado
                        descripcion += f" (Efectivo: ${monto_efectivo}, Saldo usado: ${monto_saldo_usado})"
                    
                    # Crear el movimiento de caja con el monto total
                    MovimientoCaja.objects.create(
                        fecha=pago.fecha_pago,
                        tipo=TipoMovimiento.INGRESO,
                        categoria=categoria_cuotas,
                        monto=pago.monto,  # Monto total del pago
                        descripcion=descripcion,
                        pago=pago
                    )
                
                movimientos_creados += 1
                
                if movimientos_creados % 10 == 0:
                    self.stdout.write(f'Procesados {movimientos_creados}/{total_pagos} pagos...')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Se crearían {movimientos_creados} movimientos de caja'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Sincronización completada: {movimientos_creados} movimientos de caja creados'
                )
            )
