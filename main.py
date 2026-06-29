import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QDialog
from PyQt6.QtCore import QObject, QEvent, QTimer

class InactivityFilter(QObject):
    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self.timer = timer
        
    def eventFilter(self, obj, event):
        # reiniciar temporizador ante cualquier evento de interaccion del usuario
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease,
                            QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
                            QEvent.Type.MouseMove, QEvent.Type.Wheel,
                            QEvent.Type.MouseButtonDblClick):
            self.timer.start()
        return False

from modelos.usuario_model import UsuarioModel
from vistas.LoginView import LoginView, RegistroInicialView
from controladores.LoginController import LoginController

# importes del core del sistema
from modelos.cliente_model import ClienteModel
from vistas.ClienteView import ClienteView
from controladores.ClienteController import ClienteController

from modelos.producto_model import ProductoModel
from vistas.ProductoView import ProductoView
from controladores.ProductoController import ProductoController

from modelos.factura_model import FacturaModel
from vistas.FacturaView import FacturaView
from controladores.FacturaController import FacturaController

# importes de las nuevas pantallas
from modelos.config_model import ConfigModel
from vistas.ConfigView import ConfigView
from controladores.ConfigController import ConfigController

from vistas.DashboardView import DashboardView
from controladores.DashboardController import DashboardController

from vistas.HistorialView import HistorialView
from controladores.HistorialController import HistorialController

def main():
    app = QApplication(sys.argv)

    # aca se carga el modelo del login osea las contrasenas y usuarios encryptados
    login_model = UsuarioModel()

    # aca se carga el modelo del login denuevo
    if not login_model.tiene_usuarios():
        # si la base de datos esta llimpia se inicia el asistente grafico
        registro_view = RegistroInicialView()
        login_view = LoginView()
        login_ctrl = LoginController(login_model, login_view, registro_view)
        
        # se bloquea el sistema hasta que se cree la cuenta
        if registro_view.exec() != QDialog.DialogCode.Accepted:
            return # si se cierra el asistente se cancela el programa
    else:
        # caso 2 si ya hay usuarios se va directo al login normal
        login_view = LoginView()
        login_ctrl = LoginController(login_model, login_view)

    # pantalla obligatoria de login
    if login_view.exec() != QDialog.DialogCode.Accepted:
        return # si se falla el login o cierra la ventana se cancela la ejecucion

    # establecer sesion activa del usuario en el servicio de seguridad
    usuario_autenticado = login_ctrl.get_usuario_autenticado()
    from controladores.SecurityService import SecurityService
    SecurityService.set_usuario_actual(usuario_autenticado)

    # registrar log de inicio de sesion en la auditoria
    from controladores.AuditoriaService import AuditoriaService
    AuditoriaService.registrar("INICIO_SESION", "sesion")

    # esta parte de aca se ejecuta despues de loguear con exito
    window = QMainWindow()
    window.resize(1280, 780)
    window.setWindowTitle("Sistema de Facturación Comercial - UCSM")

    central_widget = QWidget()
    main_layout = QHBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    window.setCentralWidget(central_widget)

    # se instancian los componentes mvc
    cliente_model = ClienteModel()
    cliente_view  = ClienteView()
    cliente_ctrl  = ClienteController(cliente_model, cliente_view)

    producto_model = ProductoModel()
    producto_view  = ProductoView()
    producto_ctrl  = ProductoController(producto_model, producto_view)

    factura_model = FacturaModel()
    factura_view  = FacturaView()
    factura_ctrl  = FacturaController(factura_model, factura_view, cliente_model, producto_model)

    config_model  = ConfigModel()
    config_view   = ConfigView()
    config_ctrl   = ConfigController(config_model, config_view)

    dashboard_view = DashboardView()
    dashboard_ctrl = DashboardController(factura_model, dashboard_view, cliente_model)

    historial_view = HistorialView()
    historial_ctrl = HistorialController(factura_model, historial_view)

    # se crea el stacked widget con todos los modulos
    stacked = QStackedWidget()
    stacked.addWidget(dashboard_view.contenido_widget) # 0
    stacked.addWidget(factura_view.contenido_widget)   # 1
    stacked.addWidget(historial_view.contenido_widget) # 2
    stacked.addWidget(producto_view.contenido_widget)  # 3
    stacked.addWidget(cliente_view.contenido_widget)   # 4
    stacked.addWidget(config_view.contenido_widget)    # 5

    sidebar = cliente_view.sidebar

    NAV_STYLE_NORMAL = (
        "QPushButton { color: white; background-color: transparent; text-align: left; "
        "padding: 10px; font-size: 13px; border: none; } "
        "QPushButton:hover { background-color: #2C3E6B; border-radius: 4px; }"
    )
    NAV_STYLE_ACTIVE = (
        "QPushButton { color: white; background-color: #2C3E6B; text-align: left; "
        "padding: 10px; font-size: 13px; border: none; border-radius: 4px; font-weight: bold; } "
        "QPushButton:hover { background-color: #3A4F85; border-radius: 4px; }"
    )

    nav_buttons = {
        0: cliente_view.btn_menu_dashboard,
        1: cliente_view.btn_menu_nueva_factura,
        2: cliente_view.btn_menu_historial,
        3: cliente_view.btn_menu_productos,
        4: cliente_view.btn_menu_clientes,
        5: cliente_view.btn_menu_config,
    }

    def navegar(indice: int):
        # validar que el modulo este permitido para el rol activo
        from controladores.SecurityService import SecurityService
        if indice not in SecurityService.obtener_indices_permitidos():
            return
            
        stacked.setCurrentIndex(indice)
        for idx, btn in nav_buttons.items():
            btn.setStyleSheet(NAV_STYLE_ACTIVE if idx == indice else NAV_STYLE_NORMAL)
        
        # refrescar datos en caliente al cambiar de modulo
        if indice == 0:
            dashboard_ctrl.actualizar_modulo()
        elif indice == 1:
            factura_ctrl.actualizar_modulo()
        elif indice == 2:
            historial_ctrl.actualizar_modulo()
        elif indice == 3:
            producto_ctrl.actualizar_modulo()
        elif indice == 4:
            cliente_ctrl.actualizar_modulo()
        elif indice == 5:
            config_ctrl.actualizar_modulo()

    def aplicar_permisos_sidebar():
        # oculta botones de la barra lateral no autorizados para el rol activo
        from controladores.SecurityService import SecurityService
        permitidos = SecurityService.obtener_indices_permitidos()
        for idx, btn in nav_buttons.items():
            if idx in permitidos:
                btn.setVisible(True)
            else:
                btn.setVisible(False)

    cliente_view.btn_menu_dashboard.clicked.connect(lambda: navegar(0))
    cliente_view.btn_menu_nueva_factura.clicked.connect(lambda: navegar(1))
    cliente_view.btn_menu_historial.clicked.connect(lambda: navegar(2))
    cliente_view.btn_menu_productos.clicked.connect(lambda: navegar(3))
    cliente_view.btn_menu_clientes.clicked.connect(lambda: navegar(4))
    cliente_view.btn_menu_config.clicked.connect(lambda: navegar(5))

    # aplicar permisos al inicio
    aplicar_permisos_sidebar()

    # iniciar en el modulo permitido por defecto
    from controladores.SecurityService import SecurityService
    permitidos = SecurityService.obtener_indices_permitidos()
    default_idx = 0 if 0 in permitidos else permitidos[0]
    navegar(default_idx)

    # configurar temporizador de inactividad de cinco minutos
    inactivity_timer = QTimer()
    # cinco minutos en milisegundos
    inactivity_timer.setInterval(5 * 60 * 1000)
    inactivity_timer.setSingleShot(True)

    def bloquear_pantalla():
        # bloquear pantalla por inactividad
        from controladores.SecurityService import SecurityService
        from controladores.AuditoriaService import AuditoriaService
        
        AuditoriaService.registrar("BLOQUEO_INACTIVIDAD", "sesion")
        SecurityService.set_usuario_actual(None)
        
        # limpiar campos de login para el siguiente ingreso
        login_view.input_usuario.clear()
        login_view.input_password.clear()
        
        inactivity_timer.stop()
        
        if login_view.exec() == QDialog.DialogCode.Accepted:
            usr = login_ctrl.get_usuario_autenticado()
            SecurityService.set_usuario_actual(usr)
            AuditoriaService.registrar("DESBLOQUEO_SESION", "sesion")
            aplicar_permisos_sidebar()
            
            # volver a navegar al default index tras desbloquear
            perm_desb = SecurityService.obtener_indices_permitidos()
            def_idx_desb = 0 if 0 in perm_desb else perm_desb[0]
            navegar(def_idx_desb)
            
            inactivity_timer.start()
        else:
            AuditoriaService.registrar("SALIDA_SISTEMA", "sesion")
            QApplication.quit()
            sys.exit(0)

    inactivity_timer.timeout.connect(bloquear_pantalla)

    # instalar el filtro de eventos en la aplicacion
    inactivity_filter = InactivityFilter(inactivity_timer)
    app.installEventFilter(inactivity_filter)
    inactivity_timer.start()

    main_layout.addWidget(sidebar)
    main_layout.addWidget(stacked)

    window.show()
    sys.exit(app.exec())

main()