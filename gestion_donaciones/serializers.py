from rest_framework import serializers
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


class DonanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donante
        fields = ['id', 'rut', 'nombre', 'apellido', 'tipoDonante', 'email']


class BeneficiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = ['id', 'rut', 'nombre', 'direccion', 'telefono', 'email']


class ArticuloDonadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticuloDonado
        fields = [
            'id',
            'nombreObjeto',
            'descripcion',
            'cantidad',
            'categoria',
            'unidad_medida',
            'fechaVencimiento',
        ]


class DetalleDonacionSerializer(serializers.ModelSerializer):
    articulo = ArticuloDonadoSerializer(read_only=True)
    articulo_id = serializers.PrimaryKeyRelatedField(
        source='articulo',
        queryset=ArticuloDonado.objects.all(),
        write_only=True,
        required=True,
    )

    class Meta:
        model = DetalleDonacion
        fields = ['id', 'articulo', 'articulo_id', 'cantidad']


class TrazabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trazabilidad
        fields = ['id', 'fecha', 'descripcion', 'estado']


class DonacionSerializer(serializers.ModelSerializer):
    donante = DonanteSerializer(read_only=True)
    donante_id = serializers.PrimaryKeyRelatedField(
        source='donante', queryset=Donante.objects.all(), write_only=True, required=True
    )
    detalles = DetalleDonacionSerializer(many=True, read_only=True)
    trazabilidad = TrazabilidadSerializer(many=True, read_only=True)
    uuid_seguimiento = serializers.UUIDField(read_only=True)

    class Meta:
        model = Donacion
        fields = [
            'id',
            'uuid_seguimiento',
            'donante',
            'donante_id',
            'fechaDonacion',
            'estado',
            'notas',
            'entregado',
            'detalles',
            'trazabilidad',
        ]


class DetalleEntregaSerializer(serializers.ModelSerializer):
    articulo = ArticuloDonadoSerializer(read_only=True)
    articulo_id = serializers.PrimaryKeyRelatedField(
        source='articulo', queryset=ArticuloDonado.objects.all(), write_only=True, required=True
    )
    detalle_donacion = DetalleDonacionSerializer(read_only=True)
    detalle_donacion_id = serializers.PrimaryKeyRelatedField(
        source='detalle_donacion',
        queryset=DetalleDonacion.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = DetalleEntrega
        fields = [
            'id',
            'entrega',
            'articulo',
            'articulo_id',
            'cantidad',
            'detalle_donacion',
            'detalle_donacion_id',
        ]


class EntregaSerializer(serializers.ModelSerializer):
    beneficiario = BeneficiarioSerializer(read_only=True)
    beneficiario_id = serializers.PrimaryKeyRelatedField(
        source='beneficiario', queryset=Beneficiario.objects.all(), write_only=True, required=True
    )
    detalles = DetalleEntregaSerializer(many=True, read_only=True)

    class Meta:
        model = Entrega
        fields = [
            'id',
            'beneficiario',
            'beneficiario_id',
            'nombreResponsable',
            'fechaEntrega',
            'estado',
            'notas',
            'uuid_seguimiento',
            'detalles',
        ]
