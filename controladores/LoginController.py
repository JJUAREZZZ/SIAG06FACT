from PyQt6.QtWidgets import QMessageBox

class LoginController:
    def __init__(self, model, login_view, registro_view=None):
        self.model = model
        self.view = login_view
        self.registro_view = registro_view
        
        self.view.btn_ingresar.clicked.connect(self.procesar_login)
        self.view.input_password.returnPressed.connect(self.procesar_login)
        
        if self.registro_view:
            self.registro_view.btn_registrar.clicked.connect(self.procesar_registro_inicial)

    def estilo_alerta(self, msg_box):
        """aplica un estilo forzado para evitar textos invisibles o blancos."""
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)

    def procesar_registro_inicial(self):
        nombre = self.registro_view.input_nombre.text().strip()
        username = self.registro_view.input_username.text().strip()
        password = self.registro_view.input_password.text().strip()

        if not nombre or not username or not password:
            self.mostrar_alerta("Campos vacíos", "Todos los campos son obligatorios.")
            return

        exito, msg = self.model.registrar_usuario(username, password, nombre, "Administrador")
        
        if exito:
            box = QMessageBox(self.registro_view)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle("Configuración Exitosa")
            box.setText("Administrador registrado correctamente.\nProceda a iniciar sesión.")
            self.estilo_alerta(box)
            box.exec()
            self.registro_view.accept()
        else:
            self.mostrar_alerta("Error", msg)

    def procesar_login(self):
        user_txt = self.view.input_usuario.text().strip()
        pass_txt = self.view.input_password.text().strip()

        if not user_txt or not pass_txt:
            self.mostrar_alerta("Campos requeridos", "Por favor, complete ambos campos.")
            return

        usuario_autenticado = self.model.verificar_credenciales(user_txt, pass_txt)

        if usuario_autenticado:
            # guardar usuario autenticado en la propiedad del controlador
            self.usuario_logueado = usuario_autenticado
            self.view.accept()
        else:
            self.mostrar_alerta("Acceso Denegado", "El usuario o la contraseña son incorrectos.")

    def get_usuario_autenticado(self):
        # retorna el usuario logueado en la ultima sesion exitosa
        return getattr(self, "usuario_logueado", None)

    def mostrar_alerta(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        self.estilo_alerta(msg)
        msg.exec()