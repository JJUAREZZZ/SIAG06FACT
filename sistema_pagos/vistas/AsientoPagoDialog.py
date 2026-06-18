from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QWidget, QMessageBox,
                             QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class AsientoPagoDialog(QDialog):
    def __init__(self, num_pago, num_factura, asiento, parent=None):
        super().__init__(parent)
        self.num_pago = num_pago
        self.num_factura = num_factura
        self.asiento = asiento
        self.setWindowTitle(f"Asiento Contable — Recibo {num_pago}")
        self.resize(680, 440)
        self.setStyleSheet("background-color: #F4F6F9; color: #1B2A4A;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. cabecera principal del diálogo
        header_lbl = QLabel("Consulta de Asiento Contable (Cobranzas)")
        header_lbl.setStyleSheet("color: #1B2A4A; font-size: 19px; font-weight: bold;")
        main_layout.addWidget(header_lbl)

        if not asiento:
            no_lbl = QLabel("No se encontró el asiento contable registrado para este recibo de pago.")
            no_lbl.setStyleSheet("color: #B00000; font-size: 14px; font-weight: bold; background: white; padding: 20px; border-radius: 6px; border: 1px solid #E6E9ED;")
            no_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(no_lbl)
            
            btn_close = QPushButton("Cerrar")
            btn_close.setStyleSheet("background-color: #1B2A4A; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold; border: none;")
            btn_close.clicked.connect(self.reject)
            main_layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignCenter)
            return

        # 2. panel de metadatos
        meta_frame = QFrame()
        meta_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E6E9ED; border-radius: 4px; padding: 10px;")
        meta_layout = QHBoxLayout(meta_frame)
        meta_layout.setContentsMargins(10, 8, 10, 8)
        
        def _lbl_meta(title, value):
            container = QVBoxLayout()
            container.setSpacing(2)
            t_lbl = QLabel(title.upper())
            t_lbl.setStyleSheet("color: #8A96B0; font-size: 9px; font-weight: bold; letter-spacing: 0.4px;")
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
            container.addWidget(t_lbl)
            container.addWidget(v_lbl)
            return container

        meta_layout.addLayout(_lbl_meta("N° Asiento", asiento["num_asiento"]))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Doc. Origen", f"Recibo {num_pago}"))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Factura Ref.", num_factura))
        meta_layout.addSpacing(15)
        meta_layout.addLayout(_lbl_meta("Glosa General", asiento["glosa"]))
        meta_layout.addStretch()
        
        main_layout.addWidget(meta_frame)

        # 3. grilla de cuentas contables (cuerpo)
        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["Cuenta", "Denominación / Descripción", "Debe (S/)", "Haber (S/)"])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.verticalHeader().setVisible(False)
        tabla.verticalHeader().setDefaultSectionSize(32)
        tabla.setStyleSheet("""
            QHeaderView::section {
                background-color: #1B2A4A; color: white;
                padding: 7px; font-weight: bold; font-size: 11px;
                border: none; border-right: 1px solid #2C3E6B;
            }
            QTableWidget {
                border: 1px solid #E6E9ED; border-radius: 4px;
                gridline-color: #F1F3F5; font-size: 12px; background: white;
                color: #1B2A4A;
            }
            QTableWidget::item { color: #1B2A4A; padding: 5px; }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
        """)
        
        # configurar anchos de columna
        hdr = tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        tabla.setColumnWidth(0, 70)
        tabla.setColumnWidth(2, 100)
        tabla.setColumnWidth(3, 100)

        # rellenar la tabla
        for line in asiento["detalles"]:
            row = tabla.rowCount()
            tabla.insertRow(row)
            
            c_code = QTableWidgetItem(str(line["cuenta_codigo"]))
            c_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_name = QTableWidgetItem(str(line["cuenta_nombre"]))
            
            debe_val = float(line["debe"])
            haber_val = float(line["haber"])
            
            debe_str = f"{debe_val:,.2f}" if debe_val > 0 else "—"
            haber_str = f"{haber_val:,.2f}" if haber_val > 0 else "—"
            
            c_debe = QTableWidgetItem(debe_str)
            c_debe.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            c_haber = QTableWidgetItem(haber_str)
            c_haber.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            for item in (c_code, c_name, c_debe, c_haber):
                item.setForeground(QColor("#1B2A4A"))
                
            tabla.setItem(row, 0, c_code)
            tabla.setItem(row, 1, c_name)
            tabla.setItem(row, 2, c_debe)
            tabla.setItem(row, 3, c_haber)
            
        main_layout.addWidget(tabla)

        # 4. panel de pie (totales y validación)
        footer_layout = QHBoxLayout()
        
        val_badge = QLabel("  Estado:  🟢 CUADRADO  ")
        val_badge.setStyleSheet("""
            color: #468847;
            font-size: 11px;
            font-weight: bold;
            background-color: #DFF0D8;
            border: 1px solid #D6E9C6;
            border-radius: 4px;
            padding: 4px 6px;
        """)
        footer_layout.addWidget(val_badge)
        footer_layout.addStretch()

        total_debe = float(asiento["total_debe"])
        total_haber = float(asiento["total_haber"])
        
        totals_lbl = QLabel(f"TOTALES:     Debe: S/ {total_debe:,.2f}    |    Haber: S/ {total_haber:,.2f}")
        totals_lbl.setStyleSheet("color: #1B2A4A; font-size: 13px; font-weight: bold;")
        footer_layout.addWidget(totals_lbl)
        
        main_layout.addLayout(footer_layout)

        # 5. botones inferiores
        bottom_layout = QHBoxLayout()
        self.btn_pdf = QPushButton("Imprimir / Exportar Recibo")
        self.btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FA; color: #1B2A4A;
                border: 1.5px solid #C0CCEA; border-radius: 5px;
                padding: 7px 15px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #D8E2F5; }
        """)
        self.btn_pdf.clicked.connect(self.exportar_recibo_html)
        bottom_layout.addWidget(self.btn_pdf)
        
        bottom_layout.addStretch()
        
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #1B2A4A; color: white;
                border: none; border-radius: 5px;
                padding: 7px 20px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #2C3E6B; }
        """)
        self.btn_cerrar.clicked.connect(self.accept)
        bottom_layout.addWidget(self.btn_cerrar)
        
        main_layout.addLayout(bottom_layout)
 
    def exportar_recibo_html(self):
        import webbrowser
        import os
        
        num_pago = self.num_pago
        num_factura = self.num_factura
        asiento = self.asiento
        
        if not asiento:
            QMessageBox.warning(self, "Error al Exportar", "No hay datos contables disponibles para exportar.")
            return

        detalles_html = ""
        for d in asiento["detalles"]:
            debe_val = float(d["debe"])
            haber_val = float(d["haber"])
            debe_str = f"S/ {debe_val:,.2f}" if debe_val > 0 else "—"
            haber_str = f"S/ {haber_val:,.2f}" if haber_val > 0 else "—"
            detalles_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #E6E9ED; text-align: center; font-weight: bold;">{d['cuenta_codigo']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #E6E9ED; color: #1B2A4A;">{d['cuenta_nombre']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #E6E9ED; text-align: right; font-weight: bold;">{debe_str}</td>
                <td style="padding: 10px; border-bottom: 1px solid #E6E9ED; text-align: right; font-weight: bold;">{haber_str}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Recibo de Caja {num_pago}</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #1B2A4A; background-color: #F4F6F9; }}
                .container {{ max-width: 800px; margin: auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border: 1px solid #E6E9ED; }}
                .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #1B2A4A; padding-bottom: 20px; margin-bottom: 25px; align-items: center; }}
                .company-info {{ font-size: 13px; line-height: 1.6; color: #555; }}
                .company-title {{ font-size: 16px; font-weight: bold; color: #1B2A4A; margin-bottom: 5px; }}
                .receipt-title {{ text-align: right; }}
                .receipt-title h1 {{ margin: 0; color: #70AD47; font-size: 26px; font-weight: 800; letter-spacing: 0.5px; }}
                .receipt-title p {{ margin: 5px 0 0 0; font-size: 18px; font-weight: bold; color: #1B2A4A; }}
                .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 30px; }}
                .meta-item {{ background: #F8FAFC; border: 1px solid #E6E9ED; border-radius: 5px; padding: 12px 15px; }}
                .meta-item strong {{ font-size: 10px; color: #8A96B0; display: block; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px; }}
                .meta-item span {{ font-size: 14px; font-weight: bold; color: #1B2A4A; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }}
                th {{ background-color: #1B2A4A; color: white; padding: 12px 10px; font-weight: bold; font-size: 12px; text-transform: uppercase; text-align: left; }}
                td {{ color: #444; font-size: 13px; }}
                .totals-box {{ text-align: right; margin-top: 15px; font-size: 15px; font-weight: bold; padding-top: 12px; border-top: 1.5px solid #E6E9ED; color: #1B2A4A; }}
                .badge {{ color: #468847; background-color: #DFF0D8; border: 1px solid #D6E9C6; border-radius: 4px; padding: 5px 10px; font-size: 12px; display: inline-block; font-weight: bold; text-transform: uppercase; }}
                .footer-sign {{ margin-top: 70px; display: flex; justify-content: space-between; }}
                .sign-line {{ text-align: center; width: 42%; border-top: 1.5px dashed #CCD1D9; padding-top: 10px; font-size: 12px; font-weight: bold; color: #5A6A85; text-transform: uppercase; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="company-info">
                        <div class="company-title">UNIVERSIDAD CATÓLICA DE SANTA MARÍA</div>
                        <strong>RUC:</strong> 20102030401<br>
                        <strong>Dirección:</strong> Urb. San José s/n, Umacollo, Arequipa<br>
                        <strong>Email:</strong> ucsm@email.com
                    </div>
                    <div class="receipt-title">
                        <h1>RECIBO DE CAJA</h1>
                        <p>{num_pago}</p>
                    </div>
                </div>

                <div class="meta-grid">
                    <div class="meta-item">
                        <strong>Referencia de Documento</strong>
                        <span>Cobro por Factura {num_factura}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Fecha de Emisión</strong>
                        <span>{asiento['fecha']}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Monto Recibido</strong>
                        <span>S/ {float(asiento['total_debe']):,.2f} Soles</span>
                    </div>
                    <div class="meta-item">
                        <strong>Concepto / Glosa</strong>
                        <span>{asiento['glosa']}</span>
                    </div>
                </div>

                <h3 style="border-bottom: 2px solid #70AD47; padding-bottom: 6px; color: #1B2A4A; font-size: 15px; font-weight: bold; text-transform: uppercase; margin-top: 30px;">Asiento Contable de Diario (Cobro Comercial)</h3>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 12%; text-align: center;">Cuenta</th>
                            <th style="width: 58%;">Descripción de la Cuenta</th>
                            <th style="width: 15%; text-align: right;">Debe (S/)</th>
                            <th style="text-align: right; width: 15%;">Haber (S/)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {detalles_html}
                    </tbody>
                </table>

                <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div class="badge">Estado: 🟢 Cuadrado</div>
                    <div class="totals-box">
                        TOTAL: Debe S/ {float(asiento['total_debe']):,.2f} | Haber S/ {float(asiento['total_haber']):,.2f}
                    </div>
                </div>

                <div class="footer-sign">
                    <div class="sign-line">Firma del Cajero / Responsable</div>
                    <div class="sign-line">Firma del Cliente (Conforme)</div>
                </div>
            </div>
            <script>
                // Abre el cuadro de impresión nativo del navegador automáticamente al cargar
                window.print();
            </script>
        </body>
        </html>
        """
        
        try:
            # crear directorio de recibos si no existe
            os.makedirs("recibos_emitidos", exist_ok=True)
            file_path = os.path.abspath(os.path.join("recibos_emitidos", f"recibo_{num_pago}.html"))
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html_content)
                
            webbrowser.open(f"file:///{file_path}")
            
            QMessageBox.information(
                self, 
                "Recibo Generado", 
                f"✔ El recibo de caja {num_pago} se ha generado e impreso correctamente.\n\n"
                f"Archivo guardado en:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar o abrir el recibo HTML:\n{e}")
