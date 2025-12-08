from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout 
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count, Case, When, Value, CharField, Sum
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from functools import wraps
from .models import Donante, Beneficiario, ArticuloDonado, Donacion, DetalleDonacion , Entrega, DetalleEntrega
from gestion_donaciones.emails import enviar_correo_brevo

# --------------------
# Utilidad: Manejo de sesiones para formularios
# --------------------
def save_form_to_session(request, form_name, data):
    """Guarda los datos del formulario en la sesión"""
    request.session[f'form_{form_name}'] = data


def get_form_from_session(request, form_name):
    """Recupera los datos del formulario desde la sesión"""
    return request.session.get(f'form_{form_name}', {})


def clear_form_session(request, form_name):
    """Limpia los datos del formulario de la sesión"""
    session_key = f'form_{form_name}'
    if session_key in request.session:
        del request.session[session_key]


# --------------------
# Decoradores personalizados
# --------------------
def adminapp_or_superuser_required(view_func):
    """
    Decorador que permite acceso a usuarios del grupo AdminApp o superusuarios.
    Estos usuarios tienen permisos administrativos completos en la aplicación.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if request.user.groups.filter(name='AdminApp').exists():
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('index')
    
    return wrapper


def staff_or_admin_required(view_func):
    """
    Decorador que permite acceso a Staff, AdminApp o superusuarios.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if request.user.groups.filter(name='AdminApp').exists():
            return view_func(request, *args, **kwargs)
        
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('index')
    
    return wrapper


# --------------------
# Helpers
# --------------------
def staff_required(user):
    return user.is_staff


def landing_page(request):
    """Página de inicio pública (landing page)"""
    # Si el usuario ya está autenticado, redirigir al index
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'DonacionesApp/landingpage/landing.html')


# --------------------
# Registro Root
# --------------------
def registro_root(request):
    """Permite registrar una cuenta raíz (superusuario) desde interfaz web"""
    if User.objects.filter(is_superuser=True).exists():
        messages.error(request, "Ya existe una cuenta raíz registrada.")
        return redirect('login')

    if request.method == 'POST':
        # Guardar en sesión
        save_form_to_session(request, 'registro_root', {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
        })

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('registro_root')

        # Crear el superusuario
        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_staff=True,
            is_superuser=True
        )

        # Enviar correo de confirmación al superusuario recién creado (si hay email)
        if email:
            login_url = request.build_absolute_uri(reverse('login'))
            mensaje_html = f"""
                <h2>Cuenta raíz creada</h2>
                <p>Se creó el superusuario <b>{username}</b> en el sistema DonaGest.</p>
                <p>Puedes iniciar sesión en: <a href="{login_url}">{login_url}</a></p>
                <p>Recuerda mantener este correo seguro.</p>
            """
            enviar_correo_brevo(
                destinatario=email,
                asunto="Cuenta raíz creada - DonaGest",
                mensaje_html=mensaje_html
            )

        clear_form_session(request, 'registro_root')
        messages.success(request, "Cuenta raíz creada exitosamente. Ahora puedes iniciar sesión.")
        return redirect('login')

    # GET - recuperar datos de sesión
    form_data = get_form_from_session(request, 'registro_root')
    return render(request, 'DonacionesApp/Registro/RegistroRoot.html', {'form_data': form_data})


# --------------------
# Autenticación
# --------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'DonacionesApp/Login/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# --------------------
# Vistas principales
# --------------------
@login_required
def index(request):
    ultimas_donaciones = Donacion.objects.all().order_by('-fechaDonacion')[:5]
    return render(request, "DonacionesApp/Main/Index.html", {
        'ultimas_donaciones': ultimas_donaciones
    })


@login_required
def ver_stock(request):
    busqueda = request.GET.get('busqueda', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    nivel = request.GET.get('nivel', '').strip()

    articulos = ArticuloDonado.objects.all()

    if busqueda:
        articulos = articulos.filter(
            Q(nombreObjeto__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    if categoria:
        articulos = articulos.filter(categoria=categoria)

    articulos = articulos.annotate(
        nivel_stock_calc=Case(
            When(cantidad__lte=0, then=Value('AGOTADO')),
            When(cantidad__lte=10, then=Value('BAJO')),
            When(cantidad__lte=50, then=Value('MEDIO')),
            default=Value('ALTO'),
            output_field=CharField(),
        )
    )

    if nivel:
        articulos = articulos.filter(nivel_stock_calc=nivel)

    articulos = articulos.order_by('nivel_stock_calc', 'nombreObjeto')
    total_cantidad = articulos.aggregate(total=Sum('cantidad'))['total'] or 0

    # Agrupar por categoría para mostrar en UI
    categorias_label = dict(ArticuloDonado.CATEGORIA_CHOICES)
    grouped = {}
    for art in articulos:
        key = art.categoria
        grouped.setdefault(key, {"label": categorias_label.get(key, key), "items": []})
        grouped[key]["items"].append(art)

    return render(request, 'DonacionesApp/stock/verStock.html', {
        'articulos': articulos,
        'articulos_por_categoria': grouped,
        'total_cantidad': total_cantidad,
        'categorias': ArticuloDonado.CATEGORIA_CHOICES,
        'niveles_stock': [
            ('AGOTADO', 'Agotado'),
            ('BAJO', 'Bajo'),
            ('MEDIO', 'Medio'),
            ('ALTO', 'Alto'),
        ],
        'categoria_actual': categoria,
        'nivel_actual': nivel,
        'busqueda_actual': busqueda,
    })


# --------------------
# Gestión de Usuarios - AdminApp y Superusuarios
# --------------------
@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def listar_usuarios(request):
    """Lista los usuarios activos."""
    usuarios = User.objects.filter(is_active=True).order_by('username')
    return render(request, "DonacionesApp/usuarios/ListarUsuarios.html", {
        "usuarios": usuarios,
        "papelera": False
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def crear_usuario(request):
    """Crea un nuevo usuario con rol asignado."""
    if request.method == 'POST':
        # Guardar datos en sesión
        save_form_to_session(request, 'crear_usuario', {
            'username': request.POST.get('username'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'rol': request.POST.get('rol'),
        })

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        # Validaciones básicas
        if not username or not password:
            messages.error(request, "El nombre de usuario y la contraseña son obligatorios.")
            return redirect('crear_usuario')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese nombre de usuario ya existe.")
            return redirect('crear_usuario')

        # AdminApp no puede crear superusuarios
        if not request.user.is_superuser and rol == 'admin':
            messages.error(request, "No tienes permisos para crear usuarios administradores.")
            return redirect('crear_usuario')

        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        # Asignar rol
        if rol == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif rol == 'adminapp':
            user.is_staff = False
            user.is_superuser = False
            try:
                adminapp_group = Group.objects.get(name='AdminApp')
                user.groups.add(adminapp_group)
            except Group.DoesNotExist:
                messages.warning(request, "El grupo 'AdminApp' no existe. Créelo desde el panel de administración.")
        elif rol == 'staff':
            user.is_staff = True
            try:
                staff_group = Group.objects.get(name='Staff')
                user.groups.add(staff_group)
            except Group.DoesNotExist:
                messages.warning(request, "El grupo 'Staff' no existe. Créelo desde el panel de administración.")
        else:
            user.is_staff = True
            try:
                staff_group = Group.objects.get(name='Staff')
                user.groups.add(staff_group)
            except Group.DoesNotExist:
                messages.warning(request, "El grupo 'Staff' no existe. Créelo desde el panel de administración.")

        user.save()
        
        # Limpiar sesión después del éxito
        clear_form_session(request, 'crear_usuario')
        
        messages.success(request, f"Usuario '{username}' creado exitosamente con rol '{rol or 'staff'}'.", extra_tags='usuarios')
        return redirect('listar_usuarios')

    # GET - recuperar datos de sesión
    form_data = get_form_from_session(request, 'crear_usuario')
    return render(request, "DonacionesApp/usuarios/crearUsuario.html", {'form_data': form_data})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def eliminar_usuario(request, user_id):
    """Desactiva un usuario (lo mueve a la papelera)."""
    usuario = get_object_or_404(User, id=user_id)

    if request.user == usuario:
        messages.error(request, "No puedes desactivar tu propio usuario.", extra_tags='usuarios')
        return redirect('listar_usuarios')
    
    if not request.user.is_superuser and usuario.is_superuser:
        messages.error(request, "No tienes permisos para desactivar usuarios administradores.", extra_tags='usuarios')
        return redirect('listar_usuarios')

    usuario.is_active = False
    usuario.save()
    messages.success(request, f"El usuario '{usuario.username}' ha sido movido a la papelera.", extra_tags='usuarios')
    return redirect('listar_usuarios')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def papelera_usuarios(request):
    """Muestra los usuarios desactivados."""
    usuarios_inactivos = User.objects.filter(is_active=False).order_by('username')
    return render(request, "DonacionesApp/usuarios/ListarUsuarios.html", {
        "usuarios": usuarios_inactivos,
        "papelera": True
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def restaurar_usuario(request, user_id):
    """Restaura un usuario desde la papelera."""
    usuario = get_object_or_404(User, id=user_id)
    usuario.is_active = True
    usuario.save()
    messages.success(request, f"El usuario '{usuario.username}' ha sido restaurado correctamente.", extra_tags='usuarios')
    return redirect('papelera_usuarios')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='AdminApp').exists(), login_url='index')
def eliminar_definitivo_usuario(request, user_id):
    """Elimina físicamente un usuario desde la papelera."""
    usuario = get_object_or_404(User, id=user_id)

    if usuario.is_active:
        messages.error(request, "Solo puedes eliminar definitivamente usuarios en la papelera.", extra_tags='usuarios')
        return redirect('listar_usuarios')
    
    if not request.user.is_superuser and usuario.is_superuser:
        messages.error(request, "No tienes permisos para eliminar usuarios administradores.", extra_tags='usuarios')
        return redirect('papelera_usuarios')

    usuario.delete()
    messages.success(request, f"El usuario '{usuario.username}' ha sido eliminado permanentemente.", extra_tags='usuarios')
    return redirect('papelera_usuarios')


# --------------------
# Gestión de Donaciones
# --------------------
@login_required
def listar_donaciones(request):
    donaciones = Donacion.objects.all().order_by('-fechaDonacion')
    return render(request, 'DonacionesApp/donaciones/ListarDonaciones.html', {'donaciones': donaciones})


@login_required
def registrar_donacion(request):
    if request.method == 'POST':
        if 'cancelar' in request.POST:
            messages.info(request, "Formulario cancelado. Tus datos se mantienen.")
            return redirect('listar_donaciones')

        # Guardar en sesión
        save_form_to_session(request, 'donacion', {
            'tipo_donante': request.POST.get('tipo_donante', 'INDIVIDUAL'),
            'rut_donante': request.POST.get('rut_donante', ''),
            'rut_empresa': request.POST.get('rut_empresa', ''),
            'rut_organizacion': request.POST.get('rut_organizacion', ''),
            'nombre_donante': request.POST.get('nombre_donante', ''),
            'apellido_donante': request.POST.get('apellido_donante', ''),
            'email_donante': request.POST.get('email_donante', ''),
            'telefono_donante': request.POST.get('telefono_donante', ''),
            'razon_social': request.POST.get('razon_social', ''),
            'representante': request.POST.get('representante', ''),
            'email_empresa': request.POST.get('email_empresa', ''),
            'telefono_empresa': request.POST.get('telefono_empresa', ''),
            'nombre_organizacion': request.POST.get('nombre_organizacion', ''),
            'contacto_principal': request.POST.get('contacto_principal', ''),
            'email_organizacion': request.POST.get('email_organizacion', ''),
            'telefono_organizacion': request.POST.get('telefono_organizacion', ''),
            'articulo': request.POST.getlist('articulo[]'),
            'categoria': request.POST.getlist('categoria[]'),
            'unidad_medida': request.POST.getlist('unidad_medida[]'),
            'descripcion_articulo': request.POST.getlist('descripcion_articulo[]'),
            'cantidad_donada': request.POST.getlist('cantidad_donada[]'),
            'fecha_vencimiento': request.POST.getlist('fecha_vencimiento[]'),
        })

        # Datos del donante
        tipo_donante = request.POST.get('tipo_donante', 'INDIVIDUAL')

        if tipo_donante == 'INDIVIDUAL':
            rut_donante = request.POST.get('rut_donante', '').strip()
            nombre = request.POST.get('nombre_donante', '').strip()
            apellido = request.POST.get('apellido_donante', '').strip()
            email = request.POST.get('email_donante', '').strip()
            telefono = request.POST.get('telefono_donante', '').strip()
            nombre_completo = f"{nombre} {apellido}".strip()

        elif tipo_donante == 'EMPRESA':
            rut_donante = request.POST.get('rut_empresa', '').strip()
            nombre_completo = request.POST.get('razon_social', '').strip()
            apellido = request.POST.get('representante', '').strip()
            email = request.POST.get('email_empresa', '').strip()
            telefono = request.POST.get('telefono_empresa', '').strip()

        elif tipo_donante == 'ORGANIZACION':
            rut_donante = request.POST.get('rut_organizacion', '').strip()
            nombre_completo = request.POST.get('nombre_organizacion', '').strip()
            apellido = request.POST.get('contacto_principal', '').strip()
            email = request.POST.get('email_organizacion', '').strip()
            telefono = request.POST.get('telefono_organizacion', '').strip()

        else:
            rut_donante = ""
            nombre_completo = "Donante sin nombre"
            apellido = ""
            email = ""
            telefono = ""

        # Validación
        if not rut_donante:
            messages.error(request, "El RUT del donante es obligatorio")
            return redirect('registrar_donacion')

        # Crear o recuperar donante
        donante, _ = Donante.objects.get_or_create(
            rut=rut_donante,
            defaults={
                'nombre': nombre_completo, 
                'apellido': apellido, 
                'tipoDonante': tipo_donante,
                'email': email,
                'telefono': telefono
            }
        )

        # Actualizar datos si el donante ya existía
        if email and donante.email != email:
            donante.email = email
        if telefono and donante.telefono != telefono:
            donante.telefono = telefono
        donante.save()

        # Listas de artículos
        articulos_nombres = request.POST.getlist('articulo[]')
        descripciones = request.POST.getlist('descripcion_articulo[]')
        categorias = request.POST.getlist('categoria[]')
        unidades_medida = request.POST.getlist('unidad_medida[]')
        cantidades = request.POST.getlist('cantidad_donada[]')
        fechas_vencimiento = request.POST.getlist('fecha_vencimiento[]')

        if not articulos_nombres or not cantidades or len(articulos_nombres) != len(cantidades):
            messages.error(request, "Debe ingresar al menos un artículo válido")
            return redirect('registrar_donacion')

        # 🔥 CREAR LA DONACIÓN (CABECERA)
        donacion = Donacion.objects.create(
            donante=donante,
            estado='RECIBIDO',
            notas=request.POST.get('notas_donacion', '')
        )

        productos_creados = 0
        productos_para_email = []

        # 🔥 CREAR LOS DETALLES DE DONACIÓN
        for i, nombre_art in enumerate(articulos_nombres):
            nombre_art = nombre_art.strip()
            desc = descripciones[i].strip() if i < len(descripciones) else ""
            categoria = categorias[i] if i < len(categorias) else "OTROS"
            unidad = unidades_medida[i] if i < len(unidades_medida) else "UNIDAD"
            fecha_venc = fechas_vencimiento[i] if i < len(fechas_vencimiento) else None

            try:
                cantidad = int(cantidades[i])
                if cantidad <= 0 or not nombre_art:
                    continue
            except (ValueError, TypeError, IndexError):
                continue

            # Buscar o crear artículo con los nuevos campos
            articulo_obj, _ = ArticuloDonado.objects.get_or_create(
                nombreObjeto=nombre_art,
                defaults={
                    'descripcion': desc,
                    'cantidad': 0,
                    'categoria': categoria,
                    'unidad_medida': unidad,
                    'fechaVencimiento': fecha_venc if fecha_venc else None
                }
            )

            # 🔥 CREAR DETALLE DE DONACIÓN (no Donacion directamente)
            DetalleDonacion.objects.create(
                donacion=donacion,
                articulo=articulo_obj,
                cantidad=cantidad
            )

            productos_creados += 1

            productos_para_email.append({
                "nombre": nombre_art,
                "cantidad": cantidad,
                "unidad": articulo_obj.get_unidad_medida_display()
            })

        if productos_creados == 0:
            # Si no se creó ningún detalle, eliminar la donación vacía
            donacion.delete()
            messages.error(request, "No se pudo registrar ningún artículo. Verifica los datos.")
            return redirect('registrar_donacion')

        # ================================
        # 📧 ENVIAR CORREO AL DONANTE
        # ================================
        if email:
            lista_html = "".join([
                f"<li><b>{p['nombre']}</b> - {p['cantidad']} {p['unidad'].lower()}</li>"
                for p in productos_para_email
            ])

            url_seguimiento = request.build_absolute_uri(
                reverse('seguimiento_publico', args=[donacion.uuid_seguimiento])
            )

            mensaje_html = f"""
            <h2>Gracias por tu donación, {nombre_completo}</h2>
            <p>Hemos recibido tu aporte. Estos son los artículos registrados:</p>
            <ul>
                {lista_html}
            </ul>
            <p><b>Código de seguimiento:</b> {donacion.uuid_seguimiento}</p>
            <p><a href="{url_seguimiento}">Ver el estado de mi donación</a></p>
            <p>Tu ayuda permite continuar apoyando a nuestra comunidad.</p>
            <p><b>Equipo DonaGest</b></p>
            """

            enviar_correo_brevo(
                destinatario=email,
                asunto="Confirmación de Donación - DonaGest",
                mensaje_html=mensaje_html
            )

        # Crear primer registro de trazabilidad
        donacion.actualizar_estado('RECIBIDO', f"Donación recibida con {productos_creados} artículo(s)")

        # Finalizar
        clear_form_session(request, 'donacion')
        messages.success(
            request, 
            f"✅ Donación #{donacion.id} registrada correctamente con {productos_creados} artículo(s). "
            f"Código de seguimiento: {donacion.uuid_seguimiento}"
        )
        return redirect('listar_donaciones')

    # GET
    form_data = get_form_from_session(request, 'donacion')
    return render(request, 'DonacionesApp/donaciones/agregarDonaciones.html', {'form_data': form_data})




@login_required
def ver_donacion(request, id):
    donacion = get_object_or_404(Donacion, id=id)
    return render(request, 'DonacionesApp/donaciones/verDonacion.html', {'donacion': donacion})


@login_required
@staff_or_admin_required
def editar_donacion(request, id):
    donacion = get_object_or_404(Donacion, id=id)
    detalle = donacion.detalles.first()

    if not detalle:
        messages.error(request, "La donacion no tiene detalles asociados.")
        return redirect('listar_donaciones')

    if request.method == 'POST':
        nombre_articulo = request.POST.get('articulo', '').strip()
        cantidad_donada = request.POST.get('cantidad_donada')
        nombre_donante = request.POST.get('nombre_donante', '').strip()
        apellido_donante = request.POST.get('apellido_donante', '').strip()
        tipo_donante = request.POST.get('tipo_donante', '').strip() or donacion.donante.tipoDonante

        donante = donacion.donante
        if nombre_donante:
            donante.nombre = nombre_donante
        if apellido_donante:
            donante.apellido = apellido_donante
        donante.tipoDonante = tipo_donante
        donante.save()

        if nombre_articulo:
            detalle.articulo.nombreObjeto = nombre_articulo
            detalle.articulo.save()

        try:
            cantidad_int = int(cantidad_donada)
            if cantidad_int > 0:
                detalle.cantidad = cantidad_int
                detalle.save()
        except (TypeError, ValueError):
            pass

        donacion.save()
        messages.success(request, "Donacion editada correctamente")
        return redirect('listar_donaciones')

    return render(request, 'DonacionesApp/donaciones/editarDonacion.html', {'donacion': donacion, 'detalle': detalle})


@login_required
@staff_or_admin_required
def eliminar_donacion(request, id):
    donacion = get_object_or_404(Donacion, id=id)
    if request.method == 'POST':
        donacion.delete()
        messages.success(request, "Donación eliminada correctamente")
        return redirect('listar_donaciones')
    return render(request, 'DonacionesApp/donaciones/eliminarDonacion.html', {'donacion': donacion})




@login_required
def listar_entregas(request):
    estado = request.GET.get('estado', '').strip()
    beneficiario = request.GET.get('beneficiario', '').strip()
    fecha_desde = request.GET.get('desde', '').strip()
    fecha_hasta = request.GET.get('hasta', '').strip()
    busqueda = request.GET.get('busqueda', '').strip()

    entregas_qs = Entrega.objects.all().prefetch_related('detalles__articulo', 'beneficiario')

    if estado:
        entregas_qs = entregas_qs.filter(estado=estado)

    if beneficiario:
        entregas_qs = entregas_qs.filter(beneficiario__nombre__icontains=beneficiario)

    if busqueda:
        entregas_qs = entregas_qs.filter(detalles__articulo__nombreObjeto__icontains=busqueda).distinct()

    if fecha_desde:
        entregas_qs = entregas_qs.filter(fechaEntrega__gte=fecha_desde)

    if fecha_hasta:
        entregas_qs = entregas_qs.filter(fechaEntrega__lte=fecha_hasta)

    entregas_qs = entregas_qs.order_by('-fechaEntrega')

    total_entregas = entregas_qs.count()
    total_unidades = entregas_qs.aggregate(total=Sum('detalles__cantidad'))['total'] or 0

    paginator = Paginator(entregas_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'DonacionesApp/entregas/ListarEntregas.html', {
        'page_obj': page_obj,
        'entregas': page_obj,
        'estado_actual': estado,
        'beneficiario_actual': beneficiario,
        'busqueda_actual': busqueda,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_entregas': total_entregas,
        'total_unidades': total_unidades,
        'estados_entrega': Entrega.ESTADO_CHOICES,
    })


@login_required
def registrar_entrega(request):
    if request.method == 'POST':
        if 'cancelar' in request.POST:
            messages.info(request, "Formulario cancelado.")
            return redirect('listar_entregas')

        rut_beneficiario = request.POST.get('rut_beneficiario')
        nombre_beneficiario = request.POST.get('nombre_beneficiario')
        direccion_beneficiario = request.POST.get('direccion_beneficiario')
        telefono_beneficiario = request.POST.get('telefono_beneficiario', '')
        email_beneficiario = request.POST.get('email_beneficiario', '')
        nombre_responsable = request.POST.get('nombre_responsable')

        articulos_ids = request.POST.getlist('articulo[]')
        cantidades = request.POST.getlist('cantidad[]')
        detalles_ids = request.POST.getlist('detalle_donacion_id[]')

        if not articulos_ids or not cantidades:
            messages.error(request, "Debe seleccionar al menos un producto")
            return redirect('registrar_entrega')

        if len(articulos_ids) != len(cantidades):
            messages.error(request, "Error en los datos del formulario")
            return redirect('registrar_entrega')

        try:
            cantidades = [int(c) for c in cantidades]
            if any(c <= 0 for c in cantidades):
                messages.error(request, "Las cantidades deben ser mayores a 0")
                return redirect('registrar_entrega')
        except (ValueError, TypeError):
            messages.error(request, "Cantidades inv?lidas")
            return redirect('registrar_entrega')

        beneficiario, _ = Beneficiario.objects.get_or_create(
            rut=rut_beneficiario,
            defaults={
                'nombre': nombre_beneficiario,
                'direccion': direccion_beneficiario,
                'telefono': telefono_beneficiario,
                'email': email_beneficiario
            }
        )

        errores = []
        for articulo_id, cantidad in zip(articulos_ids, cantidades):
            try:
                articulo = ArticuloDonado.objects.get(id=articulo_id)
                if articulo.cantidad < cantidad:
                    errores.append(
                        f"{articulo.nombreObjeto}: stock insuficiente "
                        f"(disponible: {articulo.cantidad}, solicitado: {cantidad})"
                    )
            except ArticuloDonado.DoesNotExist:
                errores.append(f"Art?culo con ID {articulo_id} no encontrado")

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect('registrar_entrega')

        with transaction.atomic():
            entrega = Entrega.objects.create(
                beneficiario=beneficiario,
                nombreResponsable=nombre_responsable
            )

            productos_creados = 0
            for idx, (articulo_id, cantidad) in enumerate(zip(articulos_ids, cantidades)):
                articulo = ArticuloDonado.objects.get(id=articulo_id)
                detalle_donacion_id = detalles_ids[idx] if idx < len(detalles_ids) else None
                detalle_donacion_obj = None
                if detalle_donacion_id:
                    try:
                        detalle_donacion_obj = DetalleDonacion.objects.get(id=detalle_donacion_id)
                    except DetalleDonacion.DoesNotExist:
                        detalle_donacion_obj = None

                DetalleEntrega.objects.create(
                    entrega=entrega,
                    articulo=articulo,
                    cantidad=cantidad,
                    detalle_donacion=detalle_donacion_obj,
                )
                productos_creados += 1

        clear_form_session(request, 'entrega')
        messages.success(
            request,
            f"Entrega #{entrega.id} registrada con {productos_creados} producto(s) para {nombre_beneficiario}"
        )
        return redirect('listar_entregas')

    form_data = get_form_from_session(request, 'entrega')
    articulos = ArticuloDonado.objects.filter(cantidad__gt=0).order_by('nombreObjeto')
    
    return render(request, 'DonacionesApp/entregas/agregarEntregas.html', {
        'articulos': articulos,
        'form_data': form_data
    })


@login_required
def ver_entrega(request, id):
    entrega = get_object_or_404(Entrega, id=id)
    return render(request, 'DonacionesApp/entregas/verEntrega.html', {'entrega': entrega})
@login_required
def ver_entrega(request, id):
    entrega = get_object_or_404(Entrega, id=id)
    return render(request, 'DonacionesApp/entregas/verEntrega.html', {'entrega': entrega})


def ver_seguimiento_publico(request, uuid_seguimiento):
    """
    Vista pública de seguimiento por UUID para donaciones.
    No requiere autenticación.
    """
    donacion = Donacion.objects.prefetch_related('trazabilidad', 'detalles__articulo', 'donante').filter(
        uuid_seguimiento=uuid_seguimiento
    ).first()

    return render(request, 'DonacionesApp/seguimiento/seguimiento.html', {
        'donacion': donacion,
        'uuid': uuid_seguimiento,
    })


@login_required
@staff_or_admin_required
def editar_entrega(request, id):
    entrega = get_object_or_404(Entrega, id=id)
    
    if request.method == 'POST':
        with transaction.atomic():
            entrega.beneficiario.nombre = request.POST.get('nombre_beneficiario')
            entrega.beneficiario.direccion = request.POST.get('direccion_beneficiario')
            entrega.beneficiario.telefono = request.POST.get('telefono_beneficiario', '')
            entrega.beneficiario.email = request.POST.get('email_beneficiario', '')
            entrega.beneficiario.save()
            
            entrega.nombreResponsable = request.POST.get('nombre_responsable')
            entrega.save()

            articulos_ids = request.POST.getlist('articulo[]')
            cantidades = request.POST.getlist('cantidad[]')
            detalles_ids = request.POST.getlist('detalle_donacion_id[]')

            if articulos_ids and cantidades and len(articulos_ids) == len(cantidades):
                entrega.detalles.all().delete()
                
                for idx, (articulo_id, cantidad) in enumerate(zip(articulos_ids, cantidades)):
                    try:
                        cantidad = int(cantidad)
                        if cantidad > 0:
                            articulo = ArticuloDonado.objects.get(id=articulo_id)
                            detalle_donacion_id = detalles_ids[idx] if idx < len(detalles_ids) else None
                            detalle_donacion_obj = None
                            if detalle_donacion_id:
                                try:
                                    detalle_donacion_obj = DetalleDonacion.objects.get(id=detalle_donacion_id)
                                except DetalleDonacion.DoesNotExist:
                                    detalle_donacion_obj = None

                            DetalleEntrega.objects.create(
                                entrega=entrega,
                                articulo=articulo,
                                cantidad=cantidad,
                                detalle_donacion=detalle_donacion_obj,
                            )
                    except (ValueError, ArticuloDonado.DoesNotExist):
                        pass

        messages.success(request, "Entrega editada correctamente")
        return redirect('listar_entregas')

    articulos = ArticuloDonado.objects.filter(cantidad__gt=0).order_by('nombreObjeto')
    return render(request, 'DonacionesApp/entregas/editarEntrega.html', {
        'entrega': entrega,
        'articulos': articulos
    })
@login_required
@staff_or_admin_required
def eliminar_entrega(request, id):
    entrega = get_object_or_404(Entrega, id=id)
    
    if request.method == 'POST':
        # Los detalles se eliminan en cascada y los signals restauran el stock automáticamente
        entrega.delete()
        messages.success(request, "Entrega eliminada correctamente")
        return redirect('listar_entregas')
    
    return render(request, 'DonacionesApp/entregas/eliminarEntrega.html', {'entrega': entrega})
