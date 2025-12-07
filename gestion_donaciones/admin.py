from django.contrib import admin
from .models import (
    Donante,
    Beneficiario,
    ArticuloDonado,
    Donacion,
    DetalleDonacion,
    Trazabilidad,
    Entrega,
    DetalleEntrega,
)


# ---------------------------------------------
# DONANTE
# ---------------------------------------------
@admin.register(Donante)
class DonanteAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'apellido', 'tipoDonante', 'total_donaciones']
    list_filter = ['tipoDonante']
    search_fields = ['rut', 'nombre', 'apellido']
    ordering = ['nombre']
    
    def total_donaciones(self, obj):
        return obj.donacion_set.count()
    total_donaciones.short_description = 'Total Donaciones'



# ---------------------------------------------
# BENEFICIARIO
# ---------------------------------------------
@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'direccion', 'telefono', 'email', 'total_entregas']
    search_fields = ['rut', 'nombre', 'direccion']
    ordering = ['nombre']
    
    def total_entregas(self, obj):
        return obj.entrega_set.count()
    total_entregas.short_description = 'Total Entregas'



# ---------------------------------------------
# ARTÍCULO DONADO
# ---------------------------------------------
@admin.register(ArticuloDonado)
class ArticuloDonadoAdmin(admin.ModelAdmin):
    list_display = ['nombreObjeto', 'cantidad', 'descripcion']
    search_fields = ['nombreObjeto', 'descripcion']
    ordering = ['nombreObjeto']
    list_editable = ['cantidad']



# ---------------------------------------------
# DONACIÓN
# ---------------------------------------------
@admin.register(Donacion)
class DonacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'donante_info', 'lista_articulos', 'total_cantidad', 'fechaDonacion', 'estado']
    list_filter = ['fechaDonacion', 'estado', 'donante__tipoDonante']
    search_fields = ['donante__nombre', 'donante__apellido', 'detalles__articulo__nombreObjeto']
    date_hierarchy = 'fechaDonacion'
    ordering = ['-fechaDonacion']
    inlines = []

    def get_inlines(self, request, obj=None):
        return [DetalleDonacionInline, TrazabilidadInline]

    def donante_info(self, obj):
        return f"{obj.donante.nombre} {obj.donante.apellido or ''}"
    donante_info.short_description = 'Donante'

    def lista_articulos(self, obj):
        """Muestra los artículos que forman parte de la donación"""
        return ", ".join(
            f"{d.articulo.nombreObjeto} ({d.cantidad})" 
            for d in obj.detalles.all()
        )
    lista_articulos.short_description = "Artículos"

    def total_cantidad(self, obj):
        return obj.total_cantidad
    total_cantidad.short_description = "Total Cantidades"


class DetalleDonacionInline(admin.TabularInline):
    model = DetalleDonacion
    extra = 0
    readonly_fields = ['articulo', 'cantidad']


class TrazabilidadInline(admin.TabularInline):
    model = Trazabilidad
    extra = 0
    readonly_fields = ['fecha', 'descripcion', 'estado', 'usuario']


# ---------------------------------------------
# DETALLE DE ENTREGA - Inline
# ---------------------------------------------
class DetalleEntregaInline(admin.TabularInline):
    model = DetalleEntrega
    extra = 1



# ---------------------------------------------
# ENTREGA (CABECERA)
# ---------------------------------------------
@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ['id', 'beneficiario', 'nombreResponsable', 'fechaEntrega', 'total_articulos']
    list_filter = ['fechaEntrega', 'beneficiario']
    search_fields = ['beneficiario__nombre', 'beneficiario__rut', 'nombreResponsable']
    date_hierarchy = 'fechaEntrega'
    ordering = ['-fechaEntrega']

    inlines = [DetalleEntregaInline]

    def total_articulos(self, obj):
        return sum(det.cantidad for det in obj.detalles.all())
    total_articulos.short_description = 'Total Artículos Entregados'



# Personalización del sitio admin
admin.site.site_header = "Administración de Donaciones"
admin.site.site_title = "Panel de Donaciones"
admin.site.index_title = "Bienvenido al Sistema de Gestión de Donaciones"
