from django.core.management.base import BaseCommand
from django.db import transaction
from socios.models import Pago, Cuota
import re

class Command(BaseCommand):
    help = 'Migra pagos existentes del sistema antiguo al sistema de cuotas'

    def handle(self, *args, **options):
        # Buscar pagos que tienen concepto/mes_correspondiente pero no cuota
        pagos_a_migrar = Pago.objects.filter(
            cuota__isnull=True,
            mes_correspondiente__isnull=False
        ).exclude(mes_correspondiente='')

        if not pagos_a_migrar.exists():
            self.stdout.write(
                self.style.WARNING('No hay pagos para migrar al sistema de cuotas.')
            )
            return

        self.stdout.write(f'Encontrados {pagos_a_migrar.count()} pagos para migrar...')

        pagos_migrados = 0
        pagos_error = 0
        errores = []

        with transaction.atomic():
            for pago in pagos_a_migrar:
                try:
                    # Parsear mes_correspondiente (ej: "Enero 2025", "Febrero 2024")
                    mes_str = pago.mes_correspondiente.strip()
                    
                    # Extraer mes y año
                    partes = mes_str.split()
                    if len(partes) != 2:
                        raise ValueError(f"Formato inválido: {mes_str}")
                    
                    nombre_mes, anio_str = partes
                    anio = int(anio_str)
                    
                    # Mapear nombres de meses a números
                    meses_map = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    
                    mes = meses_map.get(nombre_mes.lower())
                    if not mes:
                        raise ValueError(f"Mes no reconocido: {nombre_mes}")
                    
                    # Buscar la cuota correspondiente
                    codigo = f"{mes:02d}{str(anio)[-2:]}"
                    cuota = Cuota.objects.filter(codigo=codigo).first()
                    
                    if not cuota:
                        # Crear cuota si no existe (usando el concepto del pago)
                        cuota = Cuota.objects.create(
                            codigo=codigo,
                            mes=mes,
                            anio=anio,
                            concepto=pago.concepto,
                            monto=pago.monto,
                            activa=True
                        )
                        self.stdout.write(f'  Cuota creada: {cuota}')
                    
                    # Asignar la cuota al pago
                    pago.cuota = cuota
                    pago.save()
                    
                    pagos_migrados += 1
                    self.stdout.write(f'  ✓ Migrado: {pago.socio} - {mes_str}')
                    
                except Exception as e:
                    pagos_error += 1
                    error_msg = f'Error con pago ID {pago.id} ({pago.mes_correspondiente}): {str(e)}'
                    errores.append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {error_msg}')
                    )

        # Resumen
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Migración completada!\n'
                f'Pagos migrados exitosamente: {pagos_migrados}\n'
                f'Pagos con errores: {pagos_error}\n'
                f'Total procesados: {pagos_migrados + pagos_error}'
            )
        )
        
        if errores:
            self.stdout.write(
                self.style.WARNING(
                    f'\nErrores encontrados:\n' + '\n'.join(errores)
                )
            )
