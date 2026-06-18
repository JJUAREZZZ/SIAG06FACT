from vistas.ConfigView import FormularioUsuarioDialog
from PyQt6.QtWidgets import QMessageBox

class ConfigController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # conectar eventos de empresa
        self.view.btn_guardar_empresa.clicked.connect(self.guardar_datos_empresa)

        # conectar eventos de usuarios
        self.view.btn_añadir_usuario.clicked.connect(self.mostrar_formulario_usuario)
        self.view.btn_toggle_usuario.clicked.connect(self.alternar_estado_usuario)

        # conectar eventos de los switches de seguridad/módulos
        for key, sw in self.view.switches.items():
            # usar una función lambda capturando la clave actual para guardar el estado al hacer clic
            sw.clicked.connect(lambda checked, k=key: self.guardar_toggle(k, checked))

        # inicializar datos
        self.actualizar_modulo()

    def actualizar_modulo(self):
        try:
            # 0. cargar y poblar monedas
            monedas = self.model.obtener_monedas()
            self.view.poblar_monedas(monedas)

            # 1. cargar datos empresa
            emp_datos = self.model.obtener_datos_empresa()
            if emp_datos:
                self.view.cargar_empresa(emp_datos)

            # 2. cargar configuraciones de toggles
            configs = self.model.obtener_configuraciones()
            self.view.cargar_toggles(configs)

            # 3. cargar usuarios
            usuarios = self.model.obtener_usuarios()
            self.view.cargar_usuarios(usuarios)

            # 4. actualizar kpis inferiores
            total_usuarios = len(usuarios)
            admins = sum(1 for u in usuarios if u["rol"] == "Administrador")
            operadores = total_usuarios - admins
            self.view.lbl_val_total_usuarios.setText(f"{total_usuarios} ({admins} admin, {operadores} operadores)")

            # contar alertas (por ejemplo, usuarios inactivos o alguna alerta simulada)
            inactivos = sum(1 for u in usuarios if u.get("estado") == "Inactivo")
            self.view.lbl_val_alertas.setText(f"{inactivos} advertencia(s)" if inactivos > 0 else "0 advertencias")

        except Exception as e:
            print(f"[DEBUG ERROR] Falló la sincronización en ConfigController: {e}")

    def guardar_datos_empresa(self):
        empresa = self.view.input_empresa.text().strip()
        ruc = self.view.input_ruc.text().strip()
        direccion = self.view.input_direccion.text().strip()
        email = self.view.input_email.text().strip()
        idioma = self.view.input_idioma.text().strip()
        id_moneda_base = self.view.input_moneda.currentData()
        tasa_igv_text = self.view.input_igv.text().strip()

        if not empresa or not ruc or not direccion or not email or not tasa_igv_text:
            self.mostrar_alerta("Campos requeridos", "Por favor, complete todos los campos obligatorios.")
            return

        try:
            tasa_igv = float(tasa_igv_text)
            if not (0 <= tasa_igv <= 100):
                raise ValueError
        except ValueError:
            self.mostrar_alerta("Tasa de IGV Inválida", "La tasa de IGV debe ser un número decimal entre 0 y 100.")
            return

        exito, msg = self.model.guardar_datos_empresa(empresa, ruc, direccion, email, idioma, id_moneda_base, tasa_igv)
        if exito:
            self.mostrar_info("Configuración Guardada", msg)
            self.actualizar_modulo()
        else:
            self.mostrar_alerta("Error al Guardar", msg)

    def mostrar_formulario_usuario(self):
        dialogo = FormularioUsuarioDialog(self.view)
        if dialogo.exec() == FormularioUsuarioDialog.DialogCode.Accepted:
            nombre, username, email, password = dialogo.obtener_datos()
            
            if not nombre or not username or not password:
                self.mostrar_alerta("Campos Requeridos", "El nombre, el usuario y la contraseña son obligatorios.")
                return

            exito, msg = self.model.registrar_usuario_avanzado(nombre, username, password, "Operador", email, "Activo")
            if exito:
                self.mostrar_info("Operador Creado", "El operador se ha registrado de forma segura.")
                self.actualizar_modulo()
            else:
                self.mostrar_alerta("Error de Registro", msg)

    def alternar_estado_usuario(self):
        seleccion = self.view.obtener_usuario_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione un usuario de la tabla.")
            return

        id_usuario, estado_actual = seleccion
        
        # evitar desactivar al admin principal (id_usuario = 1) por seguridad
        if id_usuario == 1:
            self.mostrar_alerta("Seguridad", "No se puede desactivar al Administrador principal del sistema.")
            return

        nuevo_estado = "Inactivo" if estado_actual == "Activo" else "Activo"
        if self.model.cambiar_estado_usuario(id_usuario, nuevo_estado):
            print(f"[DEBUG] Estado del usuario ID {id_usuario} cambiado a {nuevo_estado}.")
            self.actualizar_modulo()
        else:
            self.mostrar_alerta("Error", "No se pudo cambiar el estado del usuario.")

    def guardar_toggle(self, clave, checked):
        valor = '1' if checked else '0'
        self.model.actualizar_configuracion(clave, valor)
        print(f"[DEBUG] Configuración '{clave}' actualizada a {valor}.")

    def estilo_alerta(self, msg_box):
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: normal; }
            QPushButton { background-color: #1B2A4A; color: white; padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 70px; border: none; }
            QPushButton:hover { background-color: #2C3E6B; }
        """)

    def mostrar_alerta(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        self.estilo_alerta(msg)
        msg.exec()

    def mostrar_info(self, titulo, mensaje):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        self.estilo_alerta(msg)
        msg.exec()
