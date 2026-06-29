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

        # conectar eventos de impresion y procesos contables
        self.view.btn_generar_ple.clicked.connect(self.generar_registro_ventas_ple)
        self.view.btn_respaldar_bd.clicked.connect(self.respaldar_base_datos)
        self.view.combo_formato_defecto.currentTextChanged.connect(self.guardar_formato_impresion)

        # conectar eventos de los switches de seguridad/modulos
        for key, sw in self.view.switches.items():
            # usar una funcion lambda capturando la clave actual para guardar el estado al hacer clic
            sw.clicked.connect(lambda checked, k=key: self.guardar_toggle(k, checked))

        # inicializar datos
        self.actualizar_modulo()

    def aplicar_permisos(self):
        # aplicar control de accesos a la interfaz de configuracion segun permisos del rol
        from controladores.SecurityService import SecurityService
        
        # backup de base de datos
        can_backup = SecurityService.tiene_permiso("backup_generar")
        self.view.btn_respaldar_bd.setVisible(can_backup)
        
        # gestion de usuarios
        can_user_create = SecurityService.tiene_permiso("usuario_crear")
        self.view.btn_añadir_usuario.setVisible(can_user_create)
        
        can_user_toggle = SecurityService.tiene_permiso("usuario_toggle")
        self.view.btn_toggle_usuario.setVisible(can_user_toggle)
        
        # guardar configuraciones de empresa
        can_config_save = SecurityService.tiene_permiso("config_guardar")
        self.view.btn_guardar_empresa.setVisible(can_config_save)

    def actualizar_modulo(self):
        try:
            self.aplicar_permisos()
            # 0. cargar y poblar monedas
            monedas = self.model.obtener_monedas()
            self.view.poblar_monedas(monedas)

            # 1. cargar datos empresa
            emp_datos = self.model.obtener_datos_empresa()
            if emp_datos:
                self.view.cargar_empresa(emp_datos)

            # 2. cargar configuraciones de toggles y formato
            configs = self.model.obtener_configuraciones()
            self.view.cargar_toggles(configs)
            
            formato_def = configs.get("formato_impresion_defecto", "Impresora Láser (A4)")
            self.view.combo_formato_defecto.setCurrentText(formato_def)

            # 3. cargar usuarios
            usuarios = self.model.obtener_usuarios()
            self.view.cargar_usuarios(usuarios)

            # 4. actualizar kpis inferiores
            total_usuarios = len(usuarios)
            admins = sum(1 for u in usuarios if u["rol"] == "Administrador")
            operadores = total_usuarios - admins
            self.view.lbl_val_total_usuarios.setText(f"{total_usuarios} ({admins} admin, {operadores} operadores)")

            # contar alertas (por ejemplo usuarios inactivos o alguna alerta simulada)
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
            nombre, username, email, password, rol = dialogo.obtener_datos()
            
            if not nombre or not username or not password:
                self.mostrar_alerta("Campos Requeridos", "El nombre, el usuario y la contraseña son obligatorios.")
                return

            exito, msg = self.model.registrar_usuario_avanzado(nombre, username, password, rol, email, "Activo")
            if exito:
                self.mostrar_info("Usuario Creado", f"El usuario {username} con rol {rol} se ha registrado de forma segura.")
                self.actualizar_modulo()
            else:
                self.mostrar_alerta("Error de Registro", msg)

    def alternar_estado_usuario(self):
        seleccion = self.view.obtener_usuario_seleccionado()
        if not seleccion:
            self.mostrar_alerta("Selección Requerida", "Por favor, seleccione un usuario de la tabla.")
            return

        id_usuario, estado_actual = seleccion
        
        # evitar desactivar al admin principal (id_usuario  1) por seguridad
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

    def generar_registro_ventas_ple(self):
        try:
            import os
            from datetime import datetime
            facturas = self.model.obtener_facturas_para_ple()
            emp_datos = self.model.obtener_datos_empresa()
            ruc = emp_datos.get("ruc", "20102030401") if emp_datos else "20102030401"
            
            libros_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "libros_electronicos")
            os.makedirs(libros_dir, exist_ok=True)
            
            ahora = datetime.now()
            periodo = ahora.strftime("%Y%m")
            filename = f"LE{ruc}{periodo}00140100001111.txt"
            filepath = os.path.join(libros_dir, filename)
            
            lines = []
            for idx, f in enumerate(facturas, start=1):
                fe_dt = datetime.strptime(f["fecha_emision"], "%Y-%m-%d")
                per_line = fe_dt.strftime("%Y%m00")
                cuo = f"M{idx:05d}"
                corr = f"A{idx:05d}"
                fecha_e = fe_dt.strftime("%d/%m/%Y")
                fecha_v = ""
                if f.get("fecha_vencimiento"):
                    try:
                        fv_dt = datetime.strptime(f["fecha_vencimiento"], "%Y-%m-%d")
                        fecha_v = fv_dt.strftime("%d/%m/%Y")
                    except Exception:
                        pass
                
                tipo_comp = "01" if "Factura" in f["tipo_documento"] else "03"
                serie = f["serie_comprobante"]
                corr_comp = str(f["correlativo_comprobante"])
                
                doc_cliente = f["dni_ruc"]
                tipo_doc_cliente = "6" if len(doc_cliente) == 11 else "1"
                nombre_cliente = f["cliente_nombre"]
                
                subtotal = f["subtotal"]
                igv = f["total_impuestos"]
                total = f["total"]
                
                if f["estado"] == "Anulada":
                    subtotal = 0.0
                    igv = 0.0
                    total = 0.0
                    nombre_cliente = "ANULADO"
                    
                estado_op = "2" if f["estado"] == "Anulada" else "1"
                
                fields = [
                    per_line, cuo, corr, fecha_e, fecha_v, tipo_comp, serie, corr_comp, "",
                    tipo_doc_cliente, doc_cliente, nombre_cliente, "0.00", f"{subtotal:.2f}",
                    "0.00", f"{igv:.2f}", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00",
                    f"{total:.2f}", "PEN", "1.000", "", "", "", "", "", "", "", estado_op
                ]
                lines.append("|".join(fields) + "|")
                
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))
                
            self.mostrar_info(
                "PLE Generado con Éxito",
                f"✔ Registro de Ventas PLE 14.1 generado correctamente.\n\n"
                f"Ubicación:\n{filepath}\n\n"
                f"Total de registros exportados: {len(lines)}"
            )
        except Exception as e:
            self.mostrar_alerta("Error en Generación PLE", f"Ocurrió un error inesperado al generar el PLE:\n{e}")

    def respaldar_base_datos(self):
        try:
            import os
            from datetime import datetime
            from PyQt6.QtWidgets import QInputDialog, QLineEdit
            
            # solicitar contrasena para cifrar el archivo de respaldo
            password, ok = QInputDialog.getText(self.view, "Cifrado de Respaldo", 
                                                 "Ingrese una contrasena para proteger la copia de seguridad:", 
                                                 QLineEdit.EchoMode.Password)
            if not ok or not password:
                self.mostrar_alerta("Cancelado", "El respaldo requiere una contrasena de cifrado.")
                return
                
            backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
            os.makedirs(backups_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # cambiar la extension a db enc para denotar archivo cifrado
            backup_filename = f"backup_facturacion_{timestamp}.db.enc"
            backup_filepath = os.path.join(backups_dir, backup_filename)
            
            exito, msg = self.model.respaldar_bd(backup_filepath, password)
            if exito:
                self.mostrar_info("Respaldo Creado", f"✔ Base de datos respaldada correctamente en:\n{backup_filepath}")
                # registrar evento en la auditoria
                from controladores.AuditoriaService import AuditoriaService
                AuditoriaService.registrar("CREAR_RESPALDO", backup_filename)
            else:
                self.mostrar_alerta("Error en Respaldo", f"No se pudo crear el respaldo de la base de datos:\n{msg}")
        except Exception as e:
            self.mostrar_alerta("Error en Respaldo", f"Ocurrió un error al preparar el respaldo:\n{e}")

    def guardar_formato_impresion(self, texto):
        self.model.actualizar_configuracion("formato_impresion_defecto", texto)
        print(f"[DEBUG] Formato de impresión por defecto actualizado a: {texto}")
