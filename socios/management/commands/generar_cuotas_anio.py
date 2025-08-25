from django.core.management.base import BaseCommand
from django.utils import timezone
from socios.models import Cuota, Concepto

class Command(BaseCommand):
    help = 'Genera cuotas para un año específico basado en conceptos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--anio',
            type=int,
            help='Año para el cual generar cuotas',
            default=timezone.now().year + 1
        )
        parser.add_argument(
            '--concepto-id',
            type=int,
            help='ID del concepto a usar (opcional)',
            default=None
        )

    def handle(self, *args, **options):
        anio = options['anio']
        concepto_id = options.get('concepto_id')
        
        self.stdout.write(f"🔄 Generando cuotas para el año {anio}")
        
        if concepto_id:
            try:
                conceptos = [Concepto.objects.get(id=concepto_id)]
            except Concepto.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Concepto con ID {concepto_id} no encontrado')
                )
                return
        else:
            # Usar todos los conceptos activos
            conceptos = Concepto.objects.filter(activo=True)
            
        if not conceptos:
            self.stdout.write(
                self.style.ERROR('No hay conceptos activos disponibles')
            )
            return
        
        cuotas_creadas = 0
        cuotas_existentes = 0
        
        for concepto in conceptos:
            self.stdout.write(f"\n📋 Procesando concepto: {concepto.nombre}")
            
            for mes in range(1, 13):
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
                    self.stdout.write(f"  ✅ {meses[mes]} {anio} - {concepto.nombre}")
                else:
                    cuotas_existentes += 1
                    if cuota.concepto != concepto:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️  {meses[mes]} {anio} ya existe con concepto diferente: {cuota.concepto.nombre}"
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado para {anio}!\n'
                f'Cuotas creadas: {cuotas_creadas}\n'
                f'Cuotas existentes: {cuotas_existentes}\n'
                f'Conceptos procesados: {len(conceptos)}'
            )
        )
