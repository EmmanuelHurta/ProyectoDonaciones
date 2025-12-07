from django.contrib import admin
from django.urls import path, include
from gestion_donaciones import views
from gestion_donaciones import api_views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# drf-spectacular
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# Router API interna
router = DefaultRouter()
router.register('api/donantes', api_views.DonanteViewSet)
router.register('api/beneficiarios', api_views.BeneficiarioViewSet)
router.register('api/articulos', api_views.ArticuloViewSet)
router.register('api/entregas', api_views.EntregaViewSet)
router.register('api/detalle-entregas', api_views.DetalleEntregaViewSet)
router.register('api/donaciones', api_views.DonacionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing
    path('', views.landing_page, name='landing'),

    # Dashboard
    path('inicio/', views.index, name='index'),

    # Registro
    path('registro-root/', views.registro_root, name='registro_root'),

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Donaciones
    path('donaciones/registrar/', views.registrar_donacion, name='registrar_donacion'),
    path('donaciones/editar/<int:id>/', views.editar_donacion, name='editar_donacion'),
    path('donaciones/eliminar/<int:id>/', views.eliminar_donacion, name='eliminar_donacion'),
    path('donaciones/ver/<int:id>/', views.ver_donacion, name='ver_donacion'),
    path('donaciones/listar/', views.listar_donaciones, name='listar_donaciones'),

    # Entregas
    path('entregas/registrar/', views.registrar_entrega, name='registrar_entrega'),
    path('entregas/listar/', views.listar_entregas, name='listar_entregas'),
    path('entregas/ver/<int:id>/', views.ver_entrega, name='ver_entrega'),
    path('entregas/editar/<int:id>/', views.editar_entrega, name='editar_entrega'),
    path('entregas/eliminar/<int:id>/', views.eliminar_entrega, name='eliminar_entrega'),
    path('seguimiento/<uuid:uuid_seguimiento>/', views.ver_seguimiento_publico, name='seguimiento_publico'),

    # Usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),

    # Papelera usuarios
    path('usuarios/papelera/', views.papelera_usuarios, name='papelera_usuarios'),
    path('usuarios/restaurar/<int:user_id>/', views.restaurar_usuario, name='restaurar_usuario'),
    path('usuarios/eliminar-definitivo/<int:user_id>/', views.eliminar_definitivo_usuario, name='eliminar_definitivo_usuario'),

    # Stock
    path('stock/', views.ver_stock, name='ver_stock'),

    # === Documentación API ===
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API REST pública de seguimiento por UUID (JSON)
    path('api/seguimiento/<uuid:uuid_seguimiento>/', api_views.api_seguimiento_publico, name='api_seguimiento_publico'),

    # Auth JWT (SimpleJWT)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Rutas de router DRF (API interna)
    path('', include(router.urls)),
]
