from django.core.management.base import BaseCommand
from django.db import transaction
from caja.models import CategoriaMovimiento, TipoMovimiento

class Command(BaseCommand):
    help = 'Crear categorías básicas para movimientos de caja'
    
    def handle(self, *args, **options):
        categorias_ingresos = [
            {
                'nombre': 'Cuotas Sociales',
                'descripcion': 'Ingresos por pagos de cuotas mensuales de socios',
            },
            {
                'nombre': 'Eventos Especiales',
                'descripcion': 'Ingresos por eventos, talleres y actividades especiales',
            },
            {
                'nombre': 'Ventas de Material',
                'descripcion': 'Ingresos por venta de material de ferromodelismo',
            },
            {
                'nombre': 'Donaciones',
                'descripcion': 'Donaciones de socios y terceros',
            },
        ]
        
        categorias_egresos = [
            {
                'nombre': 'Mantenimiento Local',
                'descripcion': 'Gastos de mantenimiento, limpieza y reparaciones del local',
            },
            {
                'nombre': 'Servicios Públicos',
                'descripcion': 'Luz, agua, gas, internet y otros servicios',
            },
            {
                'nombre': 'Material y Herramientas',
                'descripcion': 'Compra de material para actividades y herramientas',
            },
            {
                'nombre': 'Eventos y Actividades',
                'descripcion': 'Gastos organizativos de eventos y actividades del club',
            },
            {
                'nombre': 'Administración',
                'descripcion': 'Gastos administrativos, papelería, etc.',
            },
            {
                'nombre': 'Otros Gastos',
                'descripcion': 'Gastos varios no clasificados en otras categorías',
            },
        ]
        
        categorias_creadas = 0
        
        with transaction.atomic():
            # Crear categorías de ingresos
            for categoria_data in categorias_ingresos:
                categoria, created = CategoriaMovimiento.objects.get_or_create(
                    nombre=categoria_data['nombre'],
                    defaults={
                        'descripcion': categoria_data['descripcion'],
                        'tipo': TipoMovimiento.INGRESO,
                        'activo': True
                    }
                )
                if created:
                    categorias_creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Categoría de ingreso creada: {categoria.nombre}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Categoría ya existe: {categoria.nombre}')
                    )
            
            # Crear categorías de egresos
            for categoria_data in categorias_egresos:
                categoria, created = CategoriaMovimiento.objects.get_or_create(
                    nombre=categoria_data['nombre'],
                    defaults={
                        'descripcion': categoria_data['descripcion'],
                        'tipo': TipoMovimiento.EGRESO,
                        'activo': True
                    }
                )
                if created:
                    categorias_creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Categoría de egreso creada: {categoria.nombre}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Categoría ya existe: {categoria.nombre}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Comando completado: {categorias_creadas} categorías nuevas creadas'
            )
        )
