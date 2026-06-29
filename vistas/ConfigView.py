import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QLabel, QDialog, QAbstractItemView, QGridLayout, QSizePolicy, QAbstractButton, QComboBox)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QRectF, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QBrush, QPen

#
# interruptor deslizante personalizado (wow style)
#
class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._thumb_position = 3.0
        self._animation = QPropertyAnimation(self, b"thumb_position", self)
        self._animation.setDuration(120)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.toggled.connect(self._on_toggled)

    @pyqtProperty(float)
    def thumb_position(self):
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos):
        self._thumb_position = pos
        self.update()

    def _on_toggled(self, checked):
        end_pos = 23.0 if checked else 3.0
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(end_pos)
        self._animation.start()

    def sizeHint(self):
        return QSize(46, 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor("#70AD47") if self.isChecked() else QColor("#D0D5DD")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        rect = QRectF(0, 0, self.width(), self.height())
        painter.drawRoundedRect(rect, self.height() / 2, self.height() / 2)
        
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(QRectF(self._thumb_position, 3, 18, 18))


#
# formulario modal registro nuevo usuario
#
class FormularioUsuarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir nuevo usuario")
        self.setFixedSize(400, 390)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_title = QLabel("Registrar Usuario")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2A4A; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo (Obligatorio)")
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Nombre de usuario único (Obligatorio)")
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña (Obligatorio)")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.input_rol = QComboBox()
        self.input_rol.addItems(["Operador", "Administrador", "Usuario"])

        style_input = "QLineEdit { padding: 5px 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black; font-size: 13px; min-height: 28px; }"
        style_combo = """
            QComboBox { padding: 5px 8px; border: 1px solid #CCD1D9; border-radius: 4px; background: #F4F6F9; color: black; font-size: 13px; min-height: 28px; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """
        
        for inp in [self.input_nombre, self.input_username, self.input_email, self.input_password]:
            inp.setStyleSheet(style_input)
            layout.addWidget(inp)

        self.input_rol.setStyleSheet(style_combo)
        layout.addWidget(self.input_rol)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("QPushButton { background-color: #C00000; color: white; padding: 8px; border-radius: 4px; font-weight: bold; border: none; }")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar_form = QPushButton("Guardar")
        self.btn_guardar_form.setStyleSheet("QPushButton { background-color: #70AD47; color: white; padding: 8px; border-radius: 4px; font-weight: bold; border: none; }")
        self.btn_guardar_form.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar_form)
        layout.addLayout(btn_layout)

    def obtener_datos(self):
        return (
            self.input_nombre.text().strip(),
            self.input_username.text().strip(),
            self.input_email.text().strip(),
            self.input_password.text().strip(),
            self.input_rol.currentText()
        )


#
# vista principal de configuracion
#
#
# vista principal de configuracion
#
class ConfigView(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)
        falso_layout.setSpacing(0)

        self.contenido_widget = QWidget()
        self.contenido_widget.setObjectName("ContenidoWidget")
        self.contenido_widget.setStyleSheet("""
            QWidget#ContenidoWidget { background-color: #F4F6F9; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel { color: #1B2A4A; font-size: 13px; font-weight: bold; }
            QLineEdit {
                padding: 5px 8px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
            }
            QLineEdit:focus { border: 1.5px solid #1B2A4A; }
            QFrame#SeccionFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #E6E9ED;
            }
            QTableWidget {
                background-color: white;
                color: black;
                border: 1px solid #E6E9ED;
                border-radius: 4px;
            }
            QTableWidget::item { color: black; background-color: white; }
            QTableWidget::item:selected { background-color: #E6E9ED; color: #1B2A4A; }
            QHeaderView::section {
                background-color: #1B2A4A;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        self.contenido_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        contenido_layout.setSpacing(14)
        falso_layout.addWidget(self.contenido_widget)

        # cabecera
        lbl_titulo = QLabel("Configuración")
        lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 22px; font-weight: bold;")
        contenido_layout.addWidget(lbl_titulo)

        # layout columnas
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(20)

        # columna izquierda (datos empresa  roles)
        col_izq = QVBoxLayout()
        col_izq.setSpacing(14)

        # 1. datos generales de la empresa
        empresa_frame = QFrame()
        empresa_frame.setObjectName("SeccionFrame")
        empresa_lay = QVBoxLayout(empresa_frame)
        empresa_lay.setContentsMargins(15, 15, 15, 15)

        empresa_hdr = QHBoxLayout()
        empresa_hdr.addWidget(QLabel("Datos generales de la empresa", styleSheet="font-size: 15px; color: #1B2A4A;"))
        self.btn_guardar_empresa = QPushButton("Cambiar datos")
        self.btn_guardar_empresa.setStyleSheet("QPushButton { background-color: #70AD47; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #5B9337; }")
        empresa_hdr.addWidget(self.btn_guardar_empresa)
        empresa_lay.addLayout(empresa_hdr)
        empresa_lay.addSpacing(6)

        grid_emp = QGridLayout()
        grid_emp.setSpacing(8)

        self.input_empresa = QLineEdit()
        self.input_ruc = QLineEdit()
        self.input_direccion = QLineEdit()
        self.input_direccion2 = QLineEdit("n/a")
        self.input_email = QLineEdit()
        self.input_idioma = QLineEdit()
        
        self.input_moneda = QComboBox()
        self.input_moneda.setStyleSheet("""
            QComboBox { padding: 4px 7px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; font-size: 13px; min-height: 28px; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """)
        
        self.input_igv = QLineEdit()
        self.input_igv.setPlaceholderText("Ej: 18.00")

        grid_emp.addWidget(QLabel("Empresa:"), 0, 0)
        grid_emp.addWidget(self.input_empresa, 0, 1)
        grid_emp.addWidget(QLabel("RUC:"), 1, 0)
        grid_emp.addWidget(self.input_ruc, 1, 1)
        grid_emp.addWidget(QLabel("Dirección:"), 2, 0)
        grid_emp.addWidget(self.input_direccion, 2, 1)
        grid_emp.addWidget(QLabel("Dirección 2:"), 3, 0)
        grid_emp.addWidget(self.input_direccion2, 3, 1)
        grid_emp.addWidget(QLabel("Email:"), 4, 0)
        grid_emp.addWidget(self.input_email, 4, 1)
        grid_emp.addWidget(QLabel("Idioma/Región:"), 5, 0)
        grid_emp.addWidget(self.input_idioma, 5, 1)
        grid_emp.addWidget(QLabel("Moneda base:"), 6, 0)
        grid_emp.addWidget(self.input_moneda, 6, 1)
        grid_emp.addWidget(QLabel("Tasa IGV (%):"), 7, 0)
        grid_emp.addWidget(self.input_igv, 7, 1)
        grid_emp.setColumnStretch(0, 1)
        grid_emp.setColumnStretch(1, 3)
        empresa_lay.addLayout(grid_emp)
        col_izq.addWidget(empresa_frame)

        # 2. gestion de usuarios y roles
        usuarios_frame = QFrame()
        usuarios_frame.setObjectName("SeccionFrame")
        usuarios_lay = QVBoxLayout(usuarios_frame)
        usuarios_lay.setContentsMargins(15, 15, 15, 15)

        usuarios_hdr = QHBoxLayout()
        usuarios_hdr.addWidget(QLabel("Gestión de usuarios y roles", styleSheet="font-size: 15px; color: #1B2A4A;"))
        self.btn_añadir_usuario = QPushButton("Añadir usuario")
        self.btn_añadir_usuario.setStyleSheet("QPushButton { background-color: #70AD47; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #5B9337; }")
        self.btn_toggle_usuario = QPushButton("Activar / Inactivar")
        self.btn_toggle_usuario.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        usuarios_hdr.addWidget(self.btn_toggle_usuario)
        usuarios_hdr.addWidget(self.btn_añadir_usuario)
        usuarios_lay.addLayout(usuarios_hdr)
        usuarios_lay.addSpacing(6)

        self.tabla_usuarios = QTableWidget(0, 5)
        self.tabla_usuarios.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Rol", "Estado"])
        self.tabla_usuarios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_usuarios.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_usuarios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_usuarios.horizontalHeader().setStretchLastSection(True)
        self.tabla_usuarios.setFixedHeight(160)
        usuarios_lay.addWidget(self.tabla_usuarios)
        col_izq.addWidget(usuarios_frame)

        cols_layout.addLayout(col_izq, 4)

        # columna derecha (modulos y seguridad)
        col_der = QVBoxLayout()
        col_der.setSpacing(14)

        seguridad_frame = QFrame()
        seguridad_frame.setObjectName("SeccionFrame")
        seguridad_lay = QVBoxLayout(seguridad_frame)
        seguridad_lay.setContentsMargins(15, 15, 15, 15)

        seguridad_hdr = QHBoxLayout()
        seguridad_hdr.addWidget(QLabel("Módulos y seguridad", styleSheet="font-size: 15px; color: #1B2A4A;"))
        col_der.addWidget(seguridad_frame)

        impresion_frame = QFrame()
        impresion_frame.setObjectName("SeccionFrame")
        impresion_lay = QVBoxLayout(impresion_frame)
        impresion_lay.setContentsMargins(15, 15, 15, 15)
        impresion_lay.setSpacing(10)

        lbl_imp_title = QLabel("Impresión y Procesos Contables")
        lbl_imp_title.setStyleSheet("font-size: 15px; color: #1B2A4A; font-weight: bold;")
        impresion_lay.addWidget(lbl_imp_title)

        formato_layout = QHBoxLayout()
        formato_layout.addWidget(QLabel("Formato impresión por defecto:"))
        self.combo_formato_defecto = QComboBox()
        self.combo_formato_defecto.addItems(["Impresora Láser (A4)", "Impresora Térmica (Ticket 80mm)"])
        self.combo_formato_defecto.setStyleSheet("""
            QComboBox { padding: 4px 7px; border: 1px solid #CCD1D9; border-radius: 4px; background: white; color: black; font-size: 13px; min-height: 28px; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
        """)
        formato_layout.addWidget(self.combo_formato_defecto)
        impresion_lay.addLayout(formato_layout)

        self.btn_generar_ple = QPushButton("Generar Registro de Ventas PLE/SIRE")
        self.btn_generar_ple.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        impresion_lay.addWidget(self.btn_generar_ple)

        self.btn_respaldar_bd = QPushButton("Respaldar Base de Datos (SQL Dump)")
        self.btn_respaldar_bd.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        impresion_lay.addWidget(self.btn_respaldar_bd)

        col_der.addWidget(impresion_frame)

        # toggles grid
        toggles_grid = QGridLayout()
        toggles_grid.setSpacing(12)

        self.switches = {}
        features = [
            ("modulo_inventario_avanzado", "Módulo Inventario Avanzado"),
            ("modulo_reportes_analiticos", "Módulo Reportes Analíticos"),
            ("modulo_facturacion_electronica", "Módulo Facturación Electrónica"),
            ("seguridad_2fa", "Autenticación en dos pasos (2FA)"),
            ("seguridad_politica_contrasenas", "Política de Contraseñas"),
            ("seguridad_politica_seguridad", "Política de Seguridad"),
            ("seguridad_sesion_activa", "Sesión Activa"),
            ("modulo_inventario", "Módulo Inventario"),
            ("modulo_reportes", "Módulo Reportes"),
            ("modulo_facturacion", "Módulo Facturación"),
            ("modulo_clientes", "Módulo Clientes"),
            ("modulo_configuracion", "Módulo Configuración"),
        ]

        for idx, (key, label_text) in enumerate(features):
            lbl = QLabel(label_text)
            sw = ToggleSwitch()
            toggles_grid.addWidget(lbl, idx, 0)
            toggles_grid.addWidget(sw, idx, 1, Qt.AlignmentFlag.AlignRight)
            self.switches[key] = sw

        seguridad_lay.addLayout(toggles_grid)
        cols_layout.addLayout(col_der, 3)

        contenido_layout.addLayout(cols_layout)

        # bottom kpis row (mockup 5 bottom section)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        def _create_kpi_card(title, value):
            card = QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 12px;")
            lay = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #7c7c7c; font-size: 11px; font-weight: bold;")
            lay.addWidget(t_lbl)
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet("color: #1B2A4A; font-size: 16px; font-weight: bold;")
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(v_lbl)
            return card, v_lbl

        self.card_users, self.lbl_val_total_usuarios = _create_kpi_card("Total usuarios y roles", "0")
        self.card_tax, self.lbl_val_tasa_igv = _create_kpi_card("Tasa impositiva local", "18% (IGV)")
        self.card_alerts, self.lbl_val_alertas = _create_kpi_card("Alertas generales", "0 advertencias")

        kpi_layout.addWidget(self.card_users)
        kpi_layout.addWidget(self.card_tax)
        kpi_layout.addWidget(self.card_alerts)
        contenido_layout.addLayout(kpi_layout)

    def poblar_monedas(self, monedas):
        self.input_moneda.clear()
        for m in monedas:
            self.input_moneda.addItem(f"{m['codigo_iso']} ({m['simbolo']})", m["id_moneda"])

    def cargar_empresa(self, datos):
        self.input_empresa.setText(datos.get("razon_social", ""))
        self.input_ruc.setText(datos.get("ruc", ""))
        self.input_direccion.setText(datos.get("direccion", ""))
        self.input_email.setText(datos.get("email", ""))
        self.input_idioma.setText(datos.get("idioma_region", ""))
        self.input_igv.setText(f"{float(datos.get('tasa_impositiva', 18.00)):.2f}")
        
        # seleccionar la moneda base activa
        id_moneda_activa = datos.get("id_moneda_base")
        index = self.input_moneda.findData(id_moneda_activa)
        if index != -1:
            self.input_moneda.setCurrentIndex(index)
            
        self.lbl_val_tasa_igv.setText(f"{datos.get('tasa_impositiva', 18)}% (IGV)")

    def cargar_usuarios(self, usuarios):
        self.tabla_usuarios.setRowCount(0)
        for u in usuarios:
            row = self.tabla_usuarios.rowCount()
            self.tabla_usuarios.insertRow(row)
            
            id_item = QTableWidgetItem(str(u["id_usuario"]))
            nom_item = QTableWidgetItem(str(u["nombre"]))
            ema_item = QTableWidgetItem(str(u.get("email") or "—"))
            rol_item = QTableWidgetItem(str(u["rol"]))
            est_item = QTableWidgetItem(str(u.get("estado", "Activo")))
            
            # formatear estado con color
            est_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if u.get("estado") == "Inactivo":
                est_item.setForeground(QColor("#C00000"))
            else:
                est_item.setForeground(QColor("#70AD47"))

            for item in (id_item, nom_item, ema_item, rol_item):
                item.setForeground(QColor("#1B2A4A"))
                
            self.tabla_usuarios.setItem(row, 0, id_item)
            self.tabla_usuarios.setItem(row, 1, nom_item)
            self.tabla_usuarios.setItem(row, 2, ema_item)
            self.tabla_usuarios.setItem(row, 3, rol_item)
            self.tabla_usuarios.setItem(row, 4, est_item)

    def obtener_usuario_seleccionado(self):
        fila = self.tabla_usuarios.currentRow()
        if fila != -1:
            id_val = int(self.tabla_usuarios.item(fila, 0).text())
            estado = self.tabla_usuarios.item(fila, 4).text()
            return id_val, estado
        return None

    def cargar_toggles(self, configs):
        for key, sw in self.switches.items():
            val = configs.get(key, '0')
            sw.setChecked(val == '1')
