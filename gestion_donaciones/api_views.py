from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from gestion_donaciones.models import (
    Donacion,
    DetalleDonacion,
    Trazabilidad,
    Donante,
    Beneficiario,
    ArticuloDonado,
    Entrega,
    DetalleEntrega,
)
from gestion_donaciones.serializers import (
    DonacionSerializer,
    TrazabilidadSerializer,
    DonanteSerializer,
    BeneficiarioSerializer,
    ArticuloDonadoSerializer,
    EntregaSerializer,
    DetalleEntregaSerializer,
    DetalleDonacionSerializer,
)


# -----------------------
# ViewSets para admin/uso interno (requieren auth)
# -----------------------
class DonanteViewSet(viewsets.ModelViewSet):
    queryset = Donante.objects.all().order_by('nombre')
    serializer_class = DonanteSerializer
    permission_classes = [IsAuthenticated]


class BeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all().order_by('nombre')
    serializer_class = BeneficiarioSerializer
    permission_classes = [IsAuthenticated]


class ArticuloViewSet(viewsets.ModelViewSet):
    queryset = ArticuloDonado.objects.all().order_by('nombreObjeto')
    serializer_class = ArticuloDonadoSerializer
    permission_classes = [IsAuthenticated]


class EntregaViewSet(viewsets.ModelViewSet):
    queryset = Entrega.objects.all().order_by('-fechaEntrega')
    serializer_class = EntregaSerializer
    permission_classes = [IsAuthenticated]


class DetalleEntregaViewSet(viewsets.ModelViewSet):
    queryset = DetalleEntrega.objects.all()
    serializer_class = DetalleEntregaSerializer
    permission_classes = [IsAuthenticated]


# Donacion: lista, crear, recuperar por id; acciones extra: cambiar estado, agregar trazabilidad
class DonacionViewSet(viewsets.ModelViewSet):
    queryset = Donacion.objects.all().order_by('-fechaDonacion')
    serializer_class = DonacionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        detalles_data = request.data.get('detalles', [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donacion = serializer.save()

        if not isinstance(detalles_data, list) or len(detalles_data) == 0:
            donacion.delete()
            return Response(
                {"detalles": ["Se requiere al menos un articulo en la donacion."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            productos_creados = 0
            for detalle in detalles_data:
                articulo_id = detalle.get('articulo_id') or detalle.get('articulo')
                cantidad = detalle.get('cantidad')
                if articulo_id is None or cantidad is None:
                    continue

                try:
                    cantidad_int = int(cantidad)
                except (TypeError, ValueError):
                    continue

                if cantidad_int <= 0:
                    continue

                articulo = ArticuloDonado.objects.get(pk=articulo_id)
                DetalleDonacion.objects.create(
                    donacion=donacion,
                    articulo=articulo,
                    cantidad=cantidad_int,
                )
                productos_creados += 1

            if productos_creados == 0:
                donacion.delete()
                return Response(
                    {"detalles": ["No se pudieron crear detalles de donacion validos."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as exc:  # noqa: BLE001
            donacion.delete()
            return Response(
                {"detalles": [f"Error al crear detalles: {exc}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Trazabilidad.objects.create(
            donacion=donacion,
            descripcion="Donacion registrada",
            estado=donacion.estado,
        )

        output = self.get_serializer(donacion)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def agregar_trazabilidad(self, request, pk=None):
        """
        POST /api/donaciones/{pk}/agregar_trazabilidad/
        { "descripcion": "...", "estado": "Preparacion" }
        """
        donacion = self.get_object()
        serializer = TrazabilidadSerializer(data=request.data)
        if serializer.is_valid():
            estado = serializer.validated_data.get('estado')
            descripcion = serializer.validated_data.get('descripcion', '')

            if estado:
                donacion.actualizar_estado(estado, descripcion or "Estado actualizado")
            else:
                serializer.save(donacion=donacion)

            return Response(TrazabilidadSerializer(donacion.trazabilidad.last()).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='publico/uuid/(?P<uuid_seguimiento>[^/.]+)',
    )
    def publico_uuid(self, request, uuid_seguimiento=None):
        """
        Endpoint publico por UUID: /api/donaciones/publico/uuid/{uuid}/
        (retorna JSON con trazabilidad)
        """
        donacion = get_object_or_404(Donacion, uuid_seguimiento=uuid_seguimiento)
        serializer = DonacionSerializer(donacion)
        return Response(serializer.data)


# Vista publica adicional: busqueda directa por UUID (simple)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_seguimiento_donacion(request, uuid_seguimiento):
    donacion = get_object_or_404(Donacion, uuid_seguimiento=uuid_seguimiento)
    serializer = DonacionSerializer(donacion)
    return Response(serializer.data)


# Endpoint público de seguimiento (JSON)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_seguimiento_publico(request, uuid_seguimiento):
    donacion = get_object_or_404(
        Donacion.objects.prefetch_related('detalles__articulo', 'trazabilidad', 'donante'),
        uuid_seguimiento=uuid_seguimiento
    )
    return Response(DonacionSerializer(donacion).data)
