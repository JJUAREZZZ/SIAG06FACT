import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QLabel, QComboBox, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class HistorialView(QWidget):
    # senal emitida cuando el usuario cambia el estado de una factura
    cambio_estado_solicitado = pyqtSignal(str, str) # num_factura nuevo_estado

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
            QComboBox {
                padding: 4px 7px;
                border: 1px solid #CCD1D9;
                border-radius: 4px;
                background: white;
                color: black;
                font-size: 13px;
                min-height: 28px;
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

        # 1. cabecera / titulo
        self.lbl_titulo = QLabel("Historial de facturas emitidas (Filtro: mayo 2026)")
        self.lbl_titulo.setStyleSheet("color: #1B2A4A; font-size: 20px; font-weight: bold;")
        contenido_layout.addWidget(self.lbl_titulo)

        # 2. barra de filtros (mockup 2)
        filters_frame = QFrame()
        filters_frame.setObjectName("SeccionFrame")
        filters_lay = QHBoxLayout(filters_frame)
        filters_lay.setContentsMargins(15, 10, 15, 10)
        filters_lay.setSpacing(15)

        # busqueda
        bus_lay = QVBoxLayout()
        bus_lay.addWidget(QLabel("Búsqueda por número o cliente:"))
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Ej: F004-18320 o Juan Pérez...")
        bus_lay.addWidget(self.input_buscar)
        filters_lay.addLayout(bus_lay, 3)

        # filtro estado
        est_lay = QVBoxLayout()
        est_lay.addWidget(QLabel("Filtrar por estado:"))
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Ver todas", "Pagada", "Pendiente", "Anulada"])
        est_lay.addWidget(self.combo_estado)
        filters_lay.addLayout(est_lay, 2)

        # filtro fecha
        fec_lay = QVBoxLayout()
        fec_lay.addWidget(QLabel("Filtrar por fecha:"))
        self.combo_fecha = QComboBox()
        self.combo_fecha.addItems(["Ver todas", "Mayo 2026", "Junio 2026"])
        fec_lay.addWidget(self.combo_fecha)
        filters_lay.addLayout(fec_lay, 2)

        # boton cambiar estado y ver asiento
        act_lay = QVBoxLayout()
        act_lay.addWidget(QLabel("Acciones:"))
        
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(8)
        
        self.btn_cambiar_estado = QPushButton("Cambiar Estado")
        self.btn_cambiar_estado.setStyleSheet("QPushButton { background-color: #1B2A4A; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2C3E6B; }")
        
        self.btn_ver_asiento = QPushButton("Ver Asiento")
        self.btn_ver_asiento.setStyleSheet("QPushButton { background-color: #2C3E6B; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #3A4F85; }")

        self.btn_imprimir = QPushButton("Imprimir Factura")
        self.btn_imprimir.setStyleSheet("QPushButton { background-color: #70AD47; color: white; font-weight: bold; padding: 8px 12px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #5B9337; }")
        
        btn_lay.addWidget(self.btn_cambiar_estado)
        btn_lay.addWidget(self.btn_ver_asiento)
        btn_lay.addWidget(self.btn_imprimir)
        
        act_lay.addLayout(btn_lay)
        filters_lay.addLayout(act_lay, 3)

        contenido_layout.addWidget(filters_frame)

        # 3. tabla principal de historial
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["N° Factura", "Cliente", "DNI/RUC", "Fecha Emisión", "Total", "Estado", "Notas"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        contenido_layout.addWidget(self.tabla)

        # 4. fila inferior (paginacion a la izquierda totales a la derecha)
        bottom_layout = QHBoxLayout()
        
        # paginacion (mockup 2:  1 2 3 4 ... 10 )
        self.pag_layout = QHBoxLayout()
        self.pag_layout.setSpacing(6)
        
        self.btn_pag_prev = QPushButton("<")
        self.btn_pag_prev.setFixedSize(30, 30)
        self.btn_pag_prev.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_prev)
        
        self.pag_buttons = []
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; } QPushButton:hover { background: #E6E9ED; color: black; }")
            self.pag_layout.addWidget(btn)
            self.pag_buttons.append(btn)
            
        self.lbl_pag_dots = QLabel("...")
        self.lbl_pag_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pag_dots.setStyleSheet("color: #1B2A4A; font-weight: bold;")
        self.pag_layout.addWidget(self.lbl_pag_dots)
        
        self.btn_pag_last = QPushButton("10")
        self.btn_pag_last.setFixedSize(30, 30)
        self.btn_pag_last.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_last)
        self.pag_buttons.append(self.btn_pag_last)
        
        self.btn_pag_next = QPushButton(">")
        self.btn_pag_next.setFixedSize(30, 30)
        self.btn_pag_next.setStyleSheet("QPushButton { background: white; border: 1px solid #CCD1D9; color: black; border-radius: 4px; font-weight: bold; } QPushButton:hover { background: #E6E9ED; color: black; }")
        self.pag_layout.addWidget(self.btn_pag_next)
        
        bottom_layout.addLayout(self.pag_layout)
        bottom_layout.addStretch()

        # resumen estadistico (mockup 2 bottom right)
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("background-color: white; border: 1px solid #E6E9ED; border-radius: 6px; padding: 15px;")
        resumen_lay = QVBoxLayout(resumen_frame)
        resumen_lay.setSpacing(6)
        
        def _lbl_res(text):
            l = QLabel(text)
            l.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
            return l
            
        self.lbl_val_totales = _lbl_res("Ventas totales (Periodo) : 0")
        self.lbl_val_pagadas = _lbl_res("Total Pagadas : 0")
        self.lbl_val_pendientes = _lbl_res("Total pendientes: 0")
        
        resumen_lay.addWidget(self.lbl_val_totales)
        resumen_lay.addWidget(self.lbl_val_pagadas)
        resumen_lay.addWidget(self.lbl_val_pendientes)
        
        bottom_layout.addWidget(resumen_frame)
        contenido_layout.addLayout(bottom_layout)

    def cargar_tabla(self, facturas):
        self.tabla.setRowCount(0)
        font_estado = QFont("Segoe UI", 9, QFont.Weight.Bold)
        
        for f in facturas:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            num_item = QTableWidgetItem(str(f["num_factura"]))
            cli_item = QTableWidgetItem(str(f["cliente_nombre"]))
            doc_item = QTableWidgetItem(str(f.get("dni_ruc") or "—"))
            fec_item = QTableWidgetItem(str(f["fecha"]))
            simbolo = f.get("moneda_simbolo", "S/")
            tot_item = QTableWidgetItem(f"{simbolo} {float(f['total']):,.2f}")
            est_item = QTableWidgetItem(str(f["estado"]))
            not_item = QTableWidgetItem(str(f.get("notas_anulacion") or ""))
            
            est_item.setFont(font_estado)
            if f["estado"] == "Anulada":
                est_item.setForeground(QColor("#C00000"))
            elif f["estado"] == "Pendiente":
                est_item.setForeground(QColor("#E67E22"))
            else:
                est_item.setForeground(QColor("#70AD47"))

            for item in (num_item, cli_item, doc_item, fec_item, tot_item, not_item):
                item.setForeground(QColor("#1B2A4A"))
                
            self.tabla.setItem(row, 0, num_item)
            self.tabla.setItem(row, 1, cli_item)
            self.tabla.setItem(row, 2, doc_item)
            self.tabla.setItem(row, 3, fec_item)
            self.tabla.setItem(row, 4, tot_item)
            self.tabla.setItem(row, 5, est_item)
            self.tabla.setItem(row, 6, not_item)

    def obtener_factura_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila != -1:
            return self.tabla.item(fila, 0).text(), self.tabla.item(fila, 5).text()
        return None

    def actualizar_resumen(self, total_ventas, pagadas, pendientes):
        self.lbl_val_totales.setText(f"Ventas totales (Periodo) : {total_ventas}")
        self.lbl_val_pagadas.setText(f"Total Pagadas : {pagadas}")
        self.lbl_val_pendientes.setText(f"Total pendientes: {pendientes}")
