import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QFrame, QLabel, QComboBox, 
                             QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

class PagoView(QWidget):
    pago_solicitado = pyqtSignal(str, str, float, str, str) # dni_ruc, num_factura, monto, metodo, notas
    cliente_cambiado = pyqtSignal(str) # dni_ruc

    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # main fake layout
        falso_layout = QHBoxLayout(self)
        falso_layout.setContentsMargins(0, 0, 0, 0)
        falso_layout.setSpacing(0)
 
        # content widget
        self.contenido_widget = QWidget()
        self.contenido_widget.setObjectName("ContenidoWidget")
        self.contenido_widget.setStyleSheet("""
            QWidget#ContenidoWidget { background-color: #F4F6F9; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: #1B2A4A; }
            QLabel { color: #5A6A85; font-size: 13px; font-weight: bold; border: none; }
            QLineEdit {
                padding: 8px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
            }
            QLineEdit:focus { border: 1.5px solid #1B2A4A; }
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 32px;
            }
            QComboBox:focus { border: 1.5px solid #1B2A4A; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #CCD1D9;
                selection-background-color: #1B2A4A;
                selection-color: white;
                padding: 4px;
            }
            QFrame#SeccionFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #E6E9ED;
            }
        """)
        self.contenido_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenido_layout = QVBoxLayout(self.contenido_widget)
        contenido_layout.setContentsMargins(25, 20, 25, 20)
        contenido_layout.setSpacing(14)
        falso_layout.addWidget(self.contenido_widget)

        # 1. cabecera
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("Registrar Cobro a Cliente")
        lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 22px; font-weight: bold;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        
        self.lbl_num_recibo = QLabel("R001-00001")
        self.lbl_num_recibo.setStyleSheet("""
            color: #70AD47; font-size: 13px; font-weight: bold;
            background: #EAF7E2; border: 1px solid #C4E3B1;
            border-radius: 4px; padding: 4px 12px;
        """)
        header_layout.addWidget(self.lbl_num_recibo)
        contenido_layout.addLayout(header_layout)

        # 2. selección del cliente y documento (factura)
        seleccion_frame = QFrame()
        seleccion_frame.setObjectName("SeccionFrame")
        grid_sel = QGridLayout(seleccion_frame)
        grid_sel.setContentsMargins(20, 15, 20, 15)
        grid_sel.setVerticalSpacing(10)
        grid_sel.setHorizontalSpacing(20)

        lbl_info = QLabel("Paso 1: Selección del Comprobante")
        lbl_info.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold;")
        grid_sel.addWidget(lbl_info, 0, 0, 1, 2)

        grid_sel.addWidget(QLabel("CLIENTE CON DEUDA PENDIENTE:"), 1, 0)
        self.combo_cliente = QComboBox()
        self.combo_cliente.setPlaceholderText("Seleccione un cliente...")
        grid_sel.addWidget(self.combo_cliente, 1, 1)

        grid_sel.addWidget(QLabel("FACTURA PENDIENTE DE PAGO:"), 2, 0)
        self.combo_factura = QComboBox()
        self.combo_factura.setPlaceholderText("Seleccione una factura...")
        grid_sel.addWidget(self.combo_factura, 2, 1)

        grid_sel.setColumnStretch(0, 1)
        grid_sel.setColumnStretch(1, 2)
        contenido_layout.addWidget(seleccion_frame)

        # 3. datos de la factura de referencia (solo lectura)
        self.factura_frame = QFrame()
        self.factura_frame.setObjectName("SeccionFrame")
        self.factura_frame.setVisible(False)
        grid_fact = QGridLayout(self.factura_frame)
        grid_fact.setContentsMargins(20, 15, 20, 15)
        grid_fact.setVerticalSpacing(8)
        grid_fact.setHorizontalSpacing(20)

        lbl_det = QLabel("Detalle del Comprobante Seleccionado")
        lbl_det.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold;")
        grid_fact.addWidget(lbl_det, 0, 0, 1, 4)

        for col, txt in enumerate(["Fecha Emisión", "Subtotal", "Impuestos (IGV)", "Saldo Pendiente"]):
            lbl = QLabel(txt.upper())
            lbl.setStyleSheet("color: #8A96B0; font-size: 10px; font-weight: bold; letter-spacing: 0.4px;")
            grid_fact.addWidget(lbl, 1, col)

        self.lbl_fact_fecha = self._val_label()
        self.lbl_fact_subtotal = self._val_label()
        self.lbl_fact_igv = self._val_label()
        self.lbl_fact_total = self._val_label()
        self.lbl_fact_total.setStyleSheet("color: #1B2A4A; font-size: 14px; font-weight: bold; background: #EEF2FA; border: 1.5px solid #C0CCEA; border-radius: 4px; padding: 6px 10px;")

        grid_fact.addWidget(self.lbl_fact_fecha, 2, 0)
        grid_fact.addWidget(self.lbl_fact_subtotal, 2, 1)
        grid_fact.addWidget(self.lbl_fact_igv, 2, 2)
        grid_fact.addWidget(self.lbl_fact_total, 2, 3)

        grid_fact.setColumnStretch(0, 1)
        grid_fact.setColumnStretch(1, 1)
        grid_fact.setColumnStretch(2, 1)
        grid_fact.setColumnStretch(3, 1)
        contenido_layout.addWidget(self.factura_frame)

        # 4. detalles del pago (formulario)
        pago_frame = QFrame()
        pago_frame.setObjectName("SeccionFrame")
        grid_pago = QGridLayout(pago_frame)
        grid_pago.setContentsMargins(20, 15, 20, 15)
        grid_pago.setVerticalSpacing(10)
        grid_pago.setHorizontalSpacing(20)

        lbl_pago_info = QLabel("Paso 2: Registro de Cobranza (Recibo de Caja)")
        lbl_pago_info.setStyleSheet("color: #1B2A4A; font-size: 15px; font-weight: bold;")
        grid_pago.addWidget(lbl_pago_info, 0, 0, 1, 2)

        grid_pago.addWidget(QLabel("IMPORTE RECIBIDO (S/):"), 1, 0)
        self.input_monto = QLineEdit()
        self.input_monto.setStyleSheet("font-size: 14px; font-weight: bold; color: #1B2A4A; background-color: white; border: 1px solid #CCD1D9; border-radius: 4px; padding: 8px;")
        grid_pago.addWidget(self.input_monto, 1, 1)

        grid_pago.addWidget(QLabel("MÉTODO DE PAGO / COBRO:"), 2, 0)
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["Efectivo", "Transferencia Bancaria", "Tarjeta de Crédito/Débito", "Cheque", "Depósito en Cuenta"])
        grid_pago.addWidget(self.combo_metodo, 2, 1)

        grid_pago.addWidget(QLabel("GLOSA / OBSERVACIONES:"), 3, 0)
        self.input_notas = QLineEdit()
        self.input_notas.setPlaceholderText("Ej: Cancelación total de la factura F001-XXXXX")
        grid_pago.addWidget(self.input_notas, 3, 1)

        grid_pago.setColumnStretch(0, 1)
        grid_pago.setColumnStretch(1, 2)
        contenido_layout.addWidget(pago_frame)

        # 5. botones de acción
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        self.btn_cancelar = QPushButton("Limpiar")
        self.btn_cancelar.setFixedHeight(40)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background: white; color: #C00000;
                border: 1.5px solid #C00000; border-radius: 5px;
                padding: 0px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #FFF0F0; }
        """)
        
        self.btn_emitir = QPushButton("Emitir Recibo de Pago")
        self.btn_emitir.setFixedHeight(40)
        self.btn_emitir.setStyleSheet("""
            QPushButton {
                background-color: #70AD47; color: white;
                border: none; border-radius: 5px;
                padding: 0px 28px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5B9337; }
        """)
        
        btn_lay.addWidget(self.btn_cancelar)
        btn_lay.addSpacing(10)
        btn_lay.addWidget(self.btn_emitir)
        contenido_layout.addLayout(btn_lay)

        contenido_layout.addStretch()

        # connect actions
        self.combo_cliente.currentTextChanged.connect(self._on_cliente_cambiado)
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
        self.btn_emitir.clicked.connect(self._emitir_pago)

        self._datos_clientes = []
        self._datos_facturas = []

    @staticmethod
    def _val_label(texto="—"):
        lbl = QLabel(texto)
        lbl.setStyleSheet("""
            color: #1B2A4A; font-size: 13px; font-weight: normal;
            background: #F4F6F9; border: 1px solid #CCD1D9;
            border-radius: 4px; padding: 6px 10px;
        """)
        lbl.setMinimumHeight(32)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return lbl

    def cargar_clientes(self, clientes: list):
        self._datos_clientes = clientes
        self.combo_cliente.blockSignals(True)
        self.combo_cliente.clear()
        self.combo_cliente.addItem("— Seleccione un Cliente —", "")
        for c in clientes:
            self.combo_cliente.addItem(f"{c['nombre_razon_social']} ({c['dni_ruc']})", c['dni_ruc'])
        self.combo_cliente.blockSignals(False)
        self.combo_cliente.setCurrentIndex(0)
        self.limpiar_formulario()

    def cargar_facturas(self, facturas: list):
        self._datos_facturas = facturas
        self.combo_factura.blockSignals(True)
        self.combo_factura.clear()
        self.combo_factura.addItem("— Seleccione la Factura —", "")
        for f in facturas:
            saldo = f.get("saldo_restante", float(f["total"]))
            self.combo_factura.addItem(f"{f['num_factura']} (Saldo Pendiente: S/ {saldo:,.2f})", f['num_factura'])
        self.combo_factura.blockSignals(False)
        self.combo_factura.setCurrentIndex(0)
        
        self.factura_frame.setVisible(False)
        self.input_monto.clear()
        self.input_notas.clear()

    def _on_cliente_cambiado(self, text):
        dni_ruc = self.combo_cliente.currentData()
        if dni_ruc:
            self.cliente_cambiado.emit(dni_ruc)
        else:
            self.combo_factura.clear()
            self.factura_frame.setVisible(False)

    def set_factura_seleccionada(self, num_factura):
        if not num_factura:
            self.factura_frame.setVisible(False)
            return

        for f in self._datos_facturas:
            if f["num_factura"] == num_factura:
                self.lbl_fact_fecha.setText(f["fecha_emision"])
                self.lbl_fact_subtotal.setText(f"S/ {float(f['subtotal']):,.2f}")
                self.lbl_fact_igv.setText(f"S/ {float(f['total_impuestos']):,.2f}")
                
                saldo_restante = f.get("saldo_restante", float(f["total"]))
                self.lbl_fact_total.setText(f"S/ {saldo_restante:,.2f}")
                self.input_monto.setText(f"{saldo_restante:.2f}")
                self.input_notas.setText(f"Abono Factura {num_factura}")
                self.factura_frame.setVisible(True)
                break

    def limpiar_formulario(self):
        self.combo_cliente.setCurrentIndex(0)
        self.combo_factura.clear()
        self.factura_frame.setVisible(False)
        self.input_monto.clear()
        self.input_notas.clear()
        self.combo_metodo.setCurrentIndex(0)

    def _emitir_pago(self):
        from PyQt6.QtWidgets import QMessageBox
        dni_ruc = self.combo_cliente.currentData()
        num_factura = self.combo_factura.currentData()
        monto_str = self.input_monto.text().strip()
        metodo = self.combo_metodo.currentText()
        notas = self.input_notas.text().strip()

        if not dni_ruc:
            QMessageBox.warning(self, "Campos Incompletos", "Debe seleccionar un cliente con deuda pendiente.")
            return
        if not num_factura:
            QMessageBox.warning(self, "Campos Incompletos", "Debe seleccionar una factura de la lista.")
            return
        
        if not monto_str:
            QMessageBox.warning(self, "Monto Requerido", "Por favor ingrese el monto cobrado.")
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Monto Inválido", "El monto ingresado debe ser un número decimal mayor a cero.")
            return

        # buscar factura seleccionada para validar contra el saldo pendiente
        saldo_pendiente = 0.0
        for f in self._datos_facturas:
            if f["num_factura"] == num_factura:
                saldo_pendiente = f.get("saldo_restante", float(f["total"]))
                break
                
        if monto > (saldo_pendiente + 0.01):
            QMessageBox.warning(self, "Monto Excesivo", f"El monto ingresado (S/ {monto:,.2f}) supera el saldo pendiente de esta factura (S/ {saldo_pendiente:,.2f}).")
            return

        self.pago_solicitado.emit(dni_ruc, num_factura, monto, metodo, notas)
