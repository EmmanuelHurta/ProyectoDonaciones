from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

# ==========================================
# MODELOS DE DONANTES Y BENEFICIARIOS
# ==========================================

class Donante(models.Model):
    TIPO_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('EMPRESA', 'Empresa'),
        ('ORGANIZACION', 'Organización'),
    ]
    rut = models.CharField(max_length=12, unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, default="")
    tipoDonante = models.CharField(max_length=20, choices=TIPO_CHOICES, default='INDIVIDUAL')
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, default="")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Donante'
        verbose_name_plural = 'Donantes'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido}".strip()


class Beneficiario(models.Model):
    rut = models.CharField(max_length=12, unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Beneficiario'
        verbose_name_plural = 'Beneficiarios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ==========================================
# ARTÍCULOS DONADOS
# ==========================================

class ArticuloDonado(models.Model):
    CATEGORIA_CHOICES = [
        ('ALIMENTOS', 'Alimentos'),
        ('ROPA', 'Ropa y Calzado'),
        ('HIGIENE', 'Productos de Higiene'),
        ('MEDICAMENTOS', 'Medicamentos'),
        ('EDUCACION', 'Material Educativo'),
        ('ELECTRODOMESTICOS', 'Electrodomésticos'),
        ('MUEBLES', 'Muebles'),
        ('JUGUETES', 'Juguetes'),
        ('OTROS', 'Otros'),
    ]
    
    UNIDAD_CHOICES = [
        ('UNIDAD', 'Unidad(es)'),
        ('KG', 'Kilogramos'),
        ('LITRO', 'Litros'),
        ('CAJA', 'Caja(s)'),
        ('PAQUETE', 'Paquete(s)'),
        ('BOLSA', 'Bolsa(s)'),
        ('PAR', 'Par(es)'),
        ('METRO', 'Metro(s)'),
    ]
    
    nombreObjeto = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="Sin descripción")
    cantidad = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    
    # 🔥 Campos nuevos
    categoria = models.CharField(
        max_length=50, 
        choices=CATEGORIA_CHOICES, 
        default='OTROS',
        help_text="Categoría del artículo"
    )
    unidad_medida = models.CharField(
        max_length=20, 
        choices=UNIDAD_CHOICES, 
        default='UNIDAD',
        help_text="Unidad de medida para contar el artículo"
    )
    
    fechaVencimiento = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Artículo Donado'
        verbose_name_plural = 'Artículos Donados'
        ordering = ['nombreObjeto']

    def __str__(self):
        return f"{self.nombreObjeto} ({self.cantidad} {self.get_unidad_medida_display().lower()})"
    
    @property
    def cantidad_con_unidad(self):
        """Retorna cantidad formateada con su unidad"""
        unidad = self.get_unidad_medida_display().lower()
        return f"{self.cantidad} {unidad}"
    
    @property
    def nivel_stock(self):
        if self.cantidad == 0:
            return 'AGOTADO'
        elif self.cantidad <= 10:
            return 'BAJO'
        elif self.cantidad <= 50:
            return 'MEDIO'
        else:
            return 'ALTO'


# ==========================================
# 🔥 NUEVO: DONACIÓN CON MÚLTIPLES ARTÍCULOS
# ==========================================

class Donacion(models.Model):
    """
    Cabecera de la Donación - Representa UNA transacción del donante
    Puede contener múltiples artículos (DetalleDonacion)
    """
    ESTADO_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('EN_PROCESO', 'En Proceso'),
        ('ALMACENADO', 'Almacenado'),
        ('EN_ENTREGA', 'En Entrega'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    donante = models.ForeignKey(Donante, on_delete=models.CASCADE)
    fechaDonacion = models.DateField(auto_now_add=True)
    
    # UUID para seguimiento público
    uuid_seguimiento = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    
    # Estado actual de toda la donación
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='RECIBIDO'
    )
    
    notas = models.TextField(blank=True, help_text="Notas sobre la donación")
    entregado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Donación'
        verbose_name_plural = 'Donaciones'
        ordering = ['-fechaDonacion']
        indexes = [
            models.Index(fields=['uuid_seguimiento']),
            models.Index(fields=['-fechaDonacion']),
        ]

    def __str__(self):
        return f"Donación #{self.id} - {self.donante.nombre} - {self.fechaDonacion}"
    
    @property
    def total_productos(self):
        """Retorna el número de productos diferentes donados"""
        return self.detalles.count()
    
    @property
    def total_cantidad(self):
        """Retorna la cantidad total de unidades donadas"""
        return sum(detalle.cantidad for detalle in self.detalles.all())
    
    def actualizar_estado(self, nuevo_estado, descripcion=""):
        """Actualiza el estado y crea un registro de trazabilidad"""
        self.estado = nuevo_estado
        self.save()
        
        Trazabilidad.objects.create(
            donacion=self,
            estado=nuevo_estado,
            descripcion=descripcion or f"Estado cambiado a {nuevo_estado}"
        )


class DetalleDonacion(models.Model):
    """
    Detalle de cada artículo donado en una transacción
    Permite múltiples productos en una sola donación
    """
    donacion = models.ForeignKey(Donacion, on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey(ArticuloDonado, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        verbose_name = 'Detalle de Donación'
        verbose_name_plural = 'Detalles de Donaciones'
        unique_together = ['donacion', 'articulo']  # Evita duplicar el mismo artículo

    def __str__(self):
        return f"{self.articulo.nombreObjeto} - {self.cantidad} unidades"


class Trazabilidad(models.Model):
    """
    Historial de cambios de estado de cada donación
    """
    donacion = models.ForeignKey(Donacion, on_delete=models.CASCADE, related_name='trazabilidad')
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50)
    usuario = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Registro de Trazabilidad'
        verbose_name_plural = 'Registros de Trazabilidad'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.estado} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


# ==========================================
# ENTREGA Y DETALLE
# ==========================================

class Entrega(models.Model):
    """
    Cabecera de la Entrega
    Puede contener múltiples artículos (DetalleEntrega)
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE)
    nombreResponsable = models.CharField(max_length=100)
    fechaEntrega = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='COMPLETADA')
    notas = models.TextField(blank=True)
    
    uuid_seguimiento = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        ordering = ['-fechaEntrega']

    def __str__(self):
        return f"Entrega #{self.id} - {self.beneficiario.nombre} - {self.fechaEntrega}"

    @property
    def total_productos(self):
        return self.detalles.count()

    @property
    def total_cantidad(self):
        return sum(detalle.cantidad for detalle in self.detalles.all())


class DetalleEntrega(models.Model):
    """
    Detalle de cada artículo entregado
    Vinculado con DetalleDonacion para trazabilidad completa
    """
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey(ArticuloDonado, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # 🔥 Relación con el DETALLE de donación (no con Donacion directamente)
    detalle_donacion = models.ForeignKey(
        DetalleDonacion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Detalle de donación original"
    )
    
    class Meta:
        verbose_name = 'Detalle de Entrega'
        verbose_name_plural = 'Detalles de Entregas'
        unique_together = ['entrega', 'articulo']

    def __str__(self):
        return f"{self.articulo.nombreObjeto} - {self.cantidad} unidades"
    
    def save(self, *args, **kwargs):
        """
        Actualiza el estado de la donación cuando se entrega
        """
        super().save(*args, **kwargs)
        
        if self.detalle_donacion:
            donacion = self.detalle_donacion.donacion
            
            # Verificar si TODOS los detalles de esta donación fueron entregados
            todos_entregados = all(
                DetalleEntrega.objects.filter(detalle_donacion=d).exists()
                for d in donacion.detalles.all()
            )
            
            if todos_entregados and not donacion.entregado:
                donacion.actualizar_estado('ENTREGADO', 
                    f"Entregado completamente a {self.entrega.beneficiario.nombre}")
                donacion.entregado = True
                donacion.save()