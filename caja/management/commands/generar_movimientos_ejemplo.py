from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta
import random
from caja.models import MovimientoCaja, CategoriaMovimiento, TipoMovimiento

class Command(BaseCommand):
    help = 'Genera movimientos de caja de ejemplo para testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=10,
            help='Cantidad de movimientos a generar (default: 10)',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Días hacia atrás para generar movimientos (default: 30)',
        )
    
    def handle(self, *args, **options):
        cantidad = options['cantidad']
        dias = options['dias']
        
        # Verificar que existan categorías
        categorias_ingreso = CategoriaMovimiento.objects.filter(
            tipo=TipoMovimiento.INGRESO,
            activo=True
        ).exclude(nombre="Cuotas Sociales")  # Excluir cuotas que son automáticas
        
        categorias_egreso = CategoriaMovimiento.objects.filter(
            tipo=TipoMovimiento.EGRESO,
            activo=True
        )
        
        if not categorias_ingreso.exists() and not categorias_egreso.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No hay categorías disponibles. Ejecute primero: '
                    'python manage.py crear_categorias_basicas'
                )
            )
            return
        
        # Datos de ejemplo para egresos
        ejemplos_egresos = [
            ("Pago de electricidad - Mes de agosto", 8500, 15000),
            ("Compra de herramientas para taller", 12000, 25000),
            ("Mantenimiento de aire acondicionado", 18000, 35000),
            ("Papelería y materiales de oficina", 3500, 8000),
            ("Limpieza y productos de higiene", 4500, 9000),
            ("Reparación de maquetas dañadas", 6000, 15000),
            ("Compra de material didáctico", 8000, 20000),
            ("Gastos de evento mensual", 15000, 40000),
            ("Mantenimiento general del local", 10000, 25000),
            ("Compra de pintura y accesorios", 7500, 18000),
        ]
        
        # Datos de ejemplo para ingresos
        ejemplos_ingresos = [
            ("Venta de material usado", 5000, 15000),
            ("Donación de socio benefactor", 10000, 50000),
            ("Ingreso por taller especial", 8000, 25000),
            ("Venta de productos del club", 3000, 12000),
            ("Contribución extraordinaria", 15000, 40000),
            ("Ingreso por evento especial", 20000, 60000),
        ]
        
        movimientos_creados = 0
        fecha_inicio = date.today() - timedelta(days=dias)
        
        with transaction.atomic():
            for i in range(cantidad):
                # Elegir tipo de movimiento (70% egresos, 30% ingresos para ser realista)
                es_egreso = random.random() < 0.7
                
                if es_egreso and categorias_egreso.exists():
                    categoria = random.choice(categorias_egreso)
                    tipo = TipoMovimiento.EGRESO
                    descripcion_base, monto_min, monto_max = random.choice(ejemplos_egresos)
                elif categorias_ingreso.exists():
                    categoria = random.choice(categorias_ingreso)
                    tipo = TipoMovimiento.INGRESO
                    descripcion_base, monto_min, monto_max = random.choice(ejemplos_ingresos)
                else:
                    continue  # No hay categorías disponibles
                
                # Generar fecha aleatoria en el rango
                dias_random = random.randint(0, dias)
                fecha_movimiento = fecha_inicio + timedelta(days=dias_random)
                
                # Generar monto aleatorio
                monto = Decimal(random.randint(monto_min, monto_max))
                
                # Crear descripción con variación
                variaciones = [
                    f"{descripcion_base}",
                    f"{descripcion_base} - {fecha_movimiento.strftime('%B')}",
                    f"{descripcion_base} (Proveedor externo)",
                    f"{descripcion_base} - Urgente",
                ]
                descripcion = random.choice(variaciones)
                
                # Crear el movimiento
                MovimientoCaja.objects.create(
                    fecha=fecha_movimiento,
                    tipo=tipo,
                    categoria=categoria,
                    monto=monto,
                    descripcion=descripcion
                )
                
                movimientos_creados += 1
                
                if movimientos_creados % 5 == 0:
                    self.stdout.write(f'Creados {movimientos_creados}/{cantidad} movimientos...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Se crearon {movimientos_creados} movimientos de ejemplo en los últimos {dias} días'
            )
        )
        
        # Mostrar resumen
        total_ingresos = MovimientoCaja.objects.filter(
            tipo=TipoMovimiento.INGRESO,
            fecha__gte=fecha_inicio
        ).count()
        
        total_egresos = MovimientoCaja.objects.filter(
            tipo=TipoMovimiento.EGRESO,
            fecha__gte=fecha_inicio
        ).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'📊 Resumen generado: {total_ingresos} ingresos, {total_egresos} egresos'
            )
        )
