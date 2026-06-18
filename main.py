import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QDialog

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

    # aca se carga el modelo del login osea las contraseñas y usuarios encryptados
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

    # se crea el stacked widget con todos los módulos
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
        stacked.setCurrentIndex(indice)
        for idx, btn in nav_buttons.items():
            btn.setStyleSheet(NAV_STYLE_ACTIVE if idx == indice else NAV_STYLE_NORMAL)
        
        # refrescar datos en caliente al cambiar de módulo
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

    cliente_view.btn_menu_dashboard.clicked.connect(lambda: navegar(0))
    cliente_view.btn_menu_nueva_factura.clicked.connect(lambda: navegar(1))
    cliente_view.btn_menu_historial.clicked.connect(lambda: navegar(2))
    cliente_view.btn_menu_productos.clicked.connect(lambda: navegar(3))
    cliente_view.btn_menu_clientes.clicked.connect(lambda: navegar(4))
    cliente_view.btn_menu_config.clicked.connect(lambda: navegar(5))

    # iniciar en el dashboard por defecto
    navegar(0)

    main_layout.addWidget(sidebar)
    main_layout.addWidget(stacked)

    window.show()
    sys.exit(app.exec())

main()