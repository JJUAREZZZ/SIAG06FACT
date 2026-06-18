import sys
import os

# asegurar que la ruta base incluya la carpeta actual de sistema_pagos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

# importaciones mvc del sistema de pagos
from modelos.pago_model import PagoModel
from vistas.PagoView import PagoView
from controladores.PagoController import PagoController
from vistas.HistorialPagosView import HistorialPagosView
from controladores.HistorialPagosController import HistorialPagosController

def main():
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.resize(1150, 720)
    window.setWindowTitle("Sistema de Cobranza Contable — UCSM (Teoría)")

    central_widget = QWidget()
    main_layout = QHBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    window.setCentralWidget(central_widget)

    # 1. crear barra lateral (sidebar) con estilo corporativo igual al del sistema original
    sidebar = QFrame()
    sidebar.setFixedWidth(240)
    sidebar.setStyleSheet("background-color: #1B2A4A; border: none;")
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(15, 25, 15, 25)
    sidebar_layout.setSpacing(10)

    # título/logo en sidebar
    lbl_logo = QLabel("SIA COBROS")
    lbl_logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; padding-bottom: 20px; letter-spacing: 0.5px;")
    lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    sidebar_layout.addWidget(lbl_logo)

    # botones de navegación
    btn_nuevo_cobro = QPushButton("Registrar Cobro")
    btn_historial = QPushButton("Historial Recibos")

    sidebar_layout.addWidget(btn_nuevo_cobro)
    sidebar_layout.addWidget(btn_historial)
    sidebar_layout.addStretch()

    # footer en sidebar
    lbl_footer = QLabel("UCSM — Teoría Contable\nJunio 2026")
    lbl_footer.setStyleSheet("color: #8A96B0; font-size: 10px; font-weight: bold;")
    lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
    sidebar_layout.addWidget(lbl_footer)

    # 2. inicializar componentes mvc
    try:
        pago_model = PagoModel()
    except FileNotFoundError as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Base de Datos No Encontrada",
            f"No se pudo encontrar la base de datos central de facturación.\n\n"
            f"Detalle: {e}\n\n"
            "Asegúrese de ejecutar primero el sistema de facturación o el script 'seed_db.py' "
            "en la raíz del proyecto para inicializar la base de datos 'sistema_facturacion.db'."
        )
        sys.exit(1)
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Error Crítico de Inicialización",
            f"Ocurrió un error inesperado al conectar con la base de datos:\n\n{e}"
        )
        sys.exit(1)

    pago_view = PagoView()
    pago_ctrl = PagoController(pago_model, pago_view)

    hist_view = HistorialPagosView()
    hist_ctrl = HistorialPagosController(pago_model, hist_view)

    # 3. stacked widget para alternar entre paneles
    stacked = QStackedWidget()
    stacked.addWidget(pago_view.contenido_widget) # 0
    stacked.addWidget(hist_view.contenido_widget) # 1

    # estilos de botones de navegación (sidebar qss)
    NAV_STYLE_NORMAL = (
        "QPushButton { color: white; background-color: transparent; text-align: left; "
        "padding: 12px; font-size: 13px; border: none; font-weight: bold; } "
        "QPushButton:hover { background-color: #2C3E6B; border-radius: 4px; }"
    )
    NAV_STYLE_ACTIVE = (
        "QPushButton { color: white; background-color: #70AD47; text-align: left; "
        "padding: 12px; font-size: 13px; border: none; border-radius: 4px; font-weight: bold; } "
        "QPushButton:hover { background-color: #5B9337; border-radius: 4px; }"
    )

    nav_buttons = {
        0: btn_nuevo_cobro,
        1: btn_historial
    }

    def navegar(indice: int):
        stacked.setCurrentIndex(indice)
        for idx, btn in nav_buttons.items():
            btn.setStyleSheet(NAV_STYLE_ACTIVE if idx == indice else NAV_STYLE_NORMAL)
        
        # recargar en caliente
        if indice == 0:
            pago_ctrl.actualizar_modulo()
        elif indice == 1:
            hist_ctrl.actualizar_modulo()

    btn_nuevo_cobro.clicked.connect(lambda: navegar(0))
    btn_historial.clicked.connect(lambda: navegar(1))

    # iniciar en registro de cobro por defecto
    navegar(0)

    # montar layouts
    main_layout.addWidget(sidebar)
    main_layout.addWidget(stacked)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
