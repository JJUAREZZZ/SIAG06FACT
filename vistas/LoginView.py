import os
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# ventana de configuracion inicial (solo si la bd esta vacia)
class RegistroInicialView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Inicial del Sistema")
        self.setFixedSize(500, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(10)

        lbl_title = QLabel("Primer Registro de Administrador")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1B2A4A;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel("No se detectaron usuarios en el sistema. Configure la cuenta del\nadministrador principal.")
        lbl_desc.setStyleSheet("color: #7c7c7c; font-size: 12px; font-weight: normal; margin-bottom: 5px;")
        layout.addWidget(lbl_desc)

        # text inputs con plantillas puestas como ejemplos para evitar confusiones
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo del responsable (Ej: Juan Perez)")
        
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Usuario descriptivo (Ej: admin_sistema, gestor_comercial)")
        
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña segura")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        style_input = "QLineEdit { padding: 9px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black; font-size: 13px; min-height: 28px; }"
        for inp in [self.input_nombre, self.input_username, self.input_password]:
            inp.setStyleSheet(style_input)
            layout.addWidget(inp)

        layout.addSpacing(10)

        self.btn_registrar = QPushButton("Crear Cuenta y Continuar")
        self.btn_registrar.setFixedHeight(40)
        self.btn_registrar.setStyleSheet("""
            QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; border-radius: 4px; font-size: 13px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        layout.addWidget(self.btn_registrar)


# la ventana de login tradicional
class LoginView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acceso al Sistema")
        self.setFixedSize(550, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        panel_izquierdo = QFrame()
        panel_izquierdo.setStyleSheet("background-color: #1B2A4A;")
        panel_izquierdo.setFixedWidth(200)
        izq_layout = QVBoxLayout(panel_izquierdo)
        izq_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        directorio_vistas = os.path.dirname(os.path.abspath(__file__))
        ruta_logo = os.path.join(directorio_vistas, "Logosistema.png")
        
        lbl_logo = QLabel()
        pixmap = QPixmap(ruta_logo)
        if not pixmap.isNull():
            lbl_logo.setPixmap(pixmap.scaledToWidth(140, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_logo.setText("SISTEMA")
            lbl_logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        izq_layout.addWidget(lbl_logo)
        main_layout.addWidget(panel_izquierdo)

        panel_derecho = QWidget()
        panel_derecho.setStyleSheet("background-color: white;")
        der_layout = QVBoxLayout(panel_derecho)
        der_layout.setContentsMargins(30, 30, 30, 30)
        der_layout.setSpacing(12)

        lbl_bienvenida = QLabel("Iniciar Sesión")
        lbl_bienvenida.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        der_layout.addWidget(lbl_bienvenida)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario de acceso")
        
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        style_inputs = "QLineEdit { padding: 9px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black; font-size: 13px; min-height: 28px; }"
        self.input_usuario.setStyleSheet(style_inputs)
        self.input_password.setStyleSheet(style_inputs)
        
        der_layout.addWidget(self.input_usuario)
        der_layout.addWidget(self.input_password)
        der_layout.addSpacing(5)

        self.btn_ingresar = QPushButton("Ingresar al Sistema")
        self.btn_ingresar.setFixedHeight(38)
        self.btn_ingresar.setStyleSheet("""
            QPushButton { background-color: #70AD47; color: white; font-weight: bold; border-radius: 4px; font-size: 13px; border: none; }
            QPushButton:hover { background-color: #5B9337; }
        """)
        der_layout.addWidget(self.btn_ingresar)
        main_layout.addWidget(panel_derecho)