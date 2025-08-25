from django.core.management.base import BaseCommand
from django.utils import timezone
from socios.models import Cuota, Concepto

class Command(BaseCommand):
    help = 'Genera cuotas mensuales desde enero 2024 hasta el año actual + 1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--concepto',
            type=str,
            help='Nombre del concepto para las cuotas (debe existir)',
            default='Cuota Mensual'
        )

    def handle(self, *args, **options):
        concepto_nombre = options['concepto']
        
        # Buscar o crear el concepto
        concepto, created = Concepto.objects.get_or_create(
            nombre=concepto_nombre,
            defaults={
                'descripcion': 'Cuota mensual estándar',
                'monto_sugerido': 15000.00,  # Monto por defecto
                'activo': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Concepto "{concepto_nombre}" creado con monto ${concepto.monto_sugerido}')
            )
        else:
            self.stdout.write(f'Usando concepto existente: {concepto}')

        # Generar cuotas desde enero 2024 hasta diciembre del año siguiente al actual
        anio_actual = timezone.now().year
        anio_inicio = 2024
        anio_fin = anio_actual + 1
        
        cuotas_creadas = 0
        cuotas_existentes = 0

        for anio in range(anio_inicio, anio_fin + 1):
            for mes in range(1, 13):
                # No crear cuotas anteriores a enero 2024
                if anio == 2024 and mes < 1:
                    continue
                    
                codigo = f"{mes:02d}{str(anio)[-2:]}"
                
                cuota, created = Cuota.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        'mes': mes,
                        'anio': anio,
                        'concepto': concepto,
                        'monto': concepto.monto_sugerido,
                        'activa': True
                    }
                )
                
                if created:
                    cuotas_creadas += 1
                    meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                    self.stdout.write(f'  ✓ {meses[mes]} {anio} (Código: {codigo})')
                else:
                    cuotas_existentes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Proceso completado!\n'
                f'Cuotas creadas: {cuotas_creadas}\n'
                f'Cuotas existentes: {cuotas_existentes}\n'
                f'Total: {cuotas_creadas + cuotas_existentes}'
            )
        )
        
        if cuotas_creadas > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\nAhora puedes ejecutar: python manage.py migrar_pagos_a_cuotas'
                )
            )
