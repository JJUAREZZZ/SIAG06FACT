import os
import html
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPRESAS_DIR = os.path.join(BASE_DIR, "facturas_impresas")
XML_DIR = os.path.join(BASE_DIR, "xml_emitidos")

os.makedirs(IMPRESAS_DIR, exist_ok=True)
os.makedirs(XML_DIR, exist_ok=True)

def imprimir_factura_html(factura_data, formato_impresion='A4', parent_widget=None):
    # genera y abre en navegador un html estilizado para impresion
    num_factura = factura_data.get("num_factura", "F001-00000")
    empresa_nombre = factura_data.get("empresa_nombre", "UCSM S.A.")
    empresa_ruc = factura_data.get("empresa_ruc", "20102030401")
    empresa_direccion = factura_data.get("empresa_direccion", "Arequipa")
    empresa_email = factura_data.get("empresa_email", "contacto@ucsm.edu.pe")
    
    cliente_nombre = factura_data.get("cliente_nombre", "Público General")
    cliente_doc = factura_data.get("dni_ruc", "00000000")
    cliente_direccion = factura_data.get("cliente_direccion", "Dirección")
    cliente_email = factura_data.get("cliente_email", "correo@cliente.com")
    
    fecha_emision = factura_data.get("fecha_emision", datetime.now().strftime("%Y-%m-%d"))
    forma_pago = factura_data.get("forma_pago", "Contado")
    metodo_pago = factura_data.get("metodo_pago", "Efectivo")
    moneda_simbolo = factura_data.get("moneda_simbolo", "S/")
    moneda_iso = factura_data.get("moneda_iso", "PEN")
    
    subtotal = float(factura_data.get("subtotal", 0.0))
    monto_descuento = float(factura_data.get("monto_descuento", 0.0))
    total_impuestos = float(factura_data.get("total_impuestos", 0.0))
    total = float(factura_data.get("total", 0.0))
    
    items = factura_data.get("items", [])
    cuotas = factura_data.get("cuotas", [])
    tipo_doc = factura_data.get("tipo_documento", "Factura Electrónica")
    
    # renderizado condicional de formato
    if formato_impresion.lower() == 'ticket':
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Comprobante {num_factura}</title>
    <style>
        @page {{ size: 80mm auto; margin: 0; }}
        body {{
            width: 74mm;
            margin: 0;
            padding: 3mm;
            font-family: 'Courier New', Courier, monospace;
            font-size: 11px;
            color: #000;
            background-color: #fff;
        }}
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .header {{ margin-bottom: 5px; line-height: 1.2; }}
        .header h2 {{ margin: 0; font-size: 14px; font-weight: bold; }}
        .divider {{ border-top: 1px dashed #000; margin: 5px 0; }}
        .info-table {{ width: 100%; border-collapse: collapse; }}
        .info-table td {{ padding: 1px 0; vertical-align: top; }}
        .items-table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
        .items-table th {{ border-bottom: 1px dashed #000; text-align: left; padding: 2px 0; }}
        .items-table td {{ padding: 2px 0; }}
        .totales-table {{ width: 100%; margin-top: 5px; }}
        .totales-table td {{ padding: 1px 0; }}
        .footer {{ margin-top: 15px; font-size: 9px; }}
        @media print {{
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="background:#f0f0f0; padding:10px; text-align:center; margin-bottom:10px; border-radius:4px;">
        <button onclick="window.print();" style="padding:5px 15px; font-weight:bold; cursor:pointer;">Imprimir Ticket</button>
    </div>
    
    <div class="header text-center">
        <h2>{html.escape(str(empresa_nombre))}</h2>
        <div>RUC: {html.escape(str(empresa_ruc))}</div>
        <div>{html.escape(str(empresa_direccion))}</div>
        <div>{html.escape(str(empresa_email))}</div>
    </div>
    
    <div class="divider"></div>
    
    <div class="text-center" style="font-weight:bold; font-size:12px; margin: 3px 0;">
        {tipo_doc.upper()}<br>
        {num_factura}
    </div>
    
    <div class="divider"></div>
    
    <table class="info-table">
        <tr><td style="width:35%;">Fecha:</td><td>{fecha_emision}</td></tr>
        <tr><td>Cliente:</td><td>{html.escape(str(cliente_nombre))}</td></tr>
        <tr><td>Doc:</td><td>{html.escape(str(cliente_doc))}</td></tr>
        <tr><td>Dirección:</td><td>{html.escape(str(cliente_direccion))}</td></tr>
        <tr><td>Pago:</td><td>{forma_pago} {f'({metodo_pago})' if forma_pago == 'Contado' else ''}</td></tr>
    </table>
    
    <div class="divider"></div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th style="width:50%;">Desc.</th>
                <th style="width:15%; text-align:center;">Cant</th>
                <th style="width:35%; text-align:right;">Total</th>
            </tr>
        </thead>
        <tbody>
        """
        for item in items:
            desc_line = html.escape(str(item.get("producto_nombre", "Prod")))
            cant_line = item.get("cantidad", 1)
            tot_line = float(item.get("precio_unitario_historico", 0.0)) * cant_line - float(item.get("monto_descuento_linea", 0.0))
            html_content += f"""
            <tr>
                <td>{desc_line}</td>
                <td class="text-center">{cant_line}</td>
                <td class="text-right">{moneda_simbolo} {tot_line:.2f}</td>
            </tr>
            """
            
        html_content += f"""
        </tbody>
    </table>
    
    <div class="divider"></div>
    
    <table class="totales-table">
        <tr><td style="width:60%;">Subtotal:</td><td class="text-right">{moneda_simbolo} {subtotal:.2f}</td></tr>
        {f"<tr><td>Desc. Total:</td><td class='text-right'>- {moneda_simbolo} {monto_descuento:.2f}</td></tr>" if monto_descuento > 0 else ""}
        <tr><td>Impuestos (IGV):</td><td class="text-right">{moneda_simbolo} {total_impuestos:.2f}</td></tr>
        <tr style="font-weight:bold;"><td style="font-size:12px;">TOTAL:</td><td class="text-right" style="font-size:12px;">{moneda_simbolo} {total:.2f}</td></tr>
    </table>
    """
    
        if cuotas:
            html_content += f"""
            <div class="divider"></div>
            <div style="font-weight:bold; font-size:10px;">DETALLE DE CUOTAS (CRÉDITO):</div>
            <table class="info-table" style="font-size:10px; margin-top:2px;">
            """
            for c in cuotas:
                html_content += f"<tr><td>Cuota #{c.get('numero_cuota', 1)} ({c.get('fecha_vencimiento_cuota', '')}):</td><td class='text-right'>{moneda_simbolo} {float(c.get('monto_cuota', 0.0)):.2f}</td></tr>"
            html_content += "</table>"
            
        html_content += f"""
    <div class="divider"></div>
    
    <div class="text-center footer">
        Representación impresa de la Boleta/Factura Electrónica.<br>
        Consulte su validez en el portal SUNAT.<br>
        ¡Gracias por su compra!
    </div>
    
    <script>
        window.onload = function() {{
            window.print();
        }};
    </script>
</body>
</html>
"""
    else: # a4 format
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Comprobante {num_factura}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 30px;
            color: #333;
            background-color: #fff;
        }}
        .invoice-box {{
            max-width: 800px;
            margin: auto;
            border: 1px solid #eee;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            padding: 30px;
            border-radius: 8px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }}
        .company-details {{
            line-height: 1.4;
        }}
        .company-details h1 {{
            margin: 0 0 5px 0;
            font-size: 24px;
            color: #1B2A4A;
        }}
        .document-box {{
            border: 2px solid #1B2A4A;
            border-radius: 8px;
            padding: 15px 25px;
            text-align: center;
            background-color: #F8FAFC;
        }}
        .document-box h2 {{
            margin: 0 0 5px 0;
            font-size: 16px;
            color: #1B2A4A;
        }}
        .document-box .number {{
            font-size: 18px;
            font-weight: bold;
            color: #C00000;
        }}
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
        }}
        .meta-table td {{
            padding: 6px 8px;
            vertical-align: top;
        }}
        .meta-table td.label {{
            font-weight: bold;
            color: #555;
            width: 15%;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
        }}
        .items-table th {{
            background-color: #1B2A4A;
            color: white;
            text-align: left;
            padding: 10px;
            font-size: 13px;
        }}
        .items-table td {{
            padding: 10px;
            border-bottom: 1px solid #E6E9ED;
            font-size: 13px;
        }}
        .totales-wrapper {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-top: 15px;
        }}
        .cuotas-box {{
            border: 1px solid #E6E9ED;
            border-radius: 6px;
            padding: 10px 15px;
            width: 45%;
            font-size: 12px;
            background-color: #FAFCFE;
        }}
        .totales-box {{
            width: 45%;
        }}
        .totales-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .totales-table td {{
            padding: 6px 8px;
            font-size: 13px;
        }}
        .totales-table tr.total-row td {{
            font-weight: bold;
            font-size: 16px;
            color: #1B2A4A;
            border-top: 2px solid #1B2A4A;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 11px;
            color: #777;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 0; }}
            .invoice-box {{ border: none; box-shadow: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="max-width:800px; margin:0 auto 15px auto; text-align:right;">
        <button onclick="window.print();" style="padding:8px 20px; font-weight:bold; background-color:#1B2A4A; color:white; border:none; border-radius:4px; cursor:pointer;">Imprimir Factura</button>
    </div>
    
    <div class="invoice-box">
        <div class="header">
            <div class="company-details">
                <h1>{html.escape(str(empresa_nombre))}</h1>
                <div>{html.escape(str(empresa_direccion))}</div>
                <div>Email: {html.escape(str(empresa_email))}</div>
            </div>
            <div class="document-box">
                <h2>R.U.C. {html.escape(str(empresa_ruc))}</h2>
                <div style="font-weight:bold; color:#1B2A4A; text-transform:uppercase; margin-bottom:5px;">{tipo_doc}</div>
                <div class="number">{num_factura}</div>
            </div>
        </div>
        
        <table class="meta-table">
            <tr>
                <td class="label">Señor(es):</td>
                <td>{html.escape(str(cliente_nombre))}</td>
                <td class="label">Fecha Emisión:</td>
                <td>{fecha_emision}</td>
            </tr>
            <tr>
                <td class="label">RUC/DNI:</td>
                <td>{html.escape(str(cliente_doc))}</td>
                <td class="label">Forma Pago:</td>
                <td>{forma_pago} {f'({metodo_pago})' if forma_pago == 'Contado' else ''}</td>
            </tr>
            <tr>
                <td class="label">Dirección:</td>
                <td>{html.escape(str(cliente_direccion))}</td>
                <td class="label">Moneda:</td>
                <td>{moneda_iso} ({moneda_simbolo})</td>
            </tr>
        </table>
        
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width:12%;">Código</th>
                    <th style="width:50%;">Descripción</th>
                    <th style="width:10%; text-align:center;">Cant.</th>
                    <th style="width:13%; text-align:right;">P. Unit.</th>
                    <th style="width:15%; text-align:right;">Monto</th>
                </tr>
            </thead>
            <tbody>
            """
        for item in items:
            code_line = html.escape(str(item.get("producto_codigo", "Prod")))
            desc_line = html.escape(str(item.get("producto_nombre", "Prod")))
            cant_line = item.get("cantidad", 1)
            puni_line = float(item.get("precio_unitario_historico", 0.0))
            tot_line = puni_line * cant_line - float(item.get("monto_descuento_linea", 0.0))
            html_content += f"""
                <tr>
                    <td>{code_line}</td>
                    <td>{desc_line}</td>
                    <td style="text-align:center;">{cant_line}</td>
                    <td style="text-align:right;">{moneda_simbolo} {puni_line:.2f}</td>
                    <td style="text-align:right;">{moneda_simbolo} {tot_line:.2f}</td>
                </tr>
            """
            
        html_content += f"""
            </tbody>
        </table>
        
        <div class="totales-wrapper">
            """
        if cuotas:
            html_content += f"""
            <div class="cuotas-box">
                <div style="font-weight:bold; color:#1B2A4A; margin-bottom:8px;">Información de Crédito (Cuotas)</div>
                <table style="width:100%; border-collapse:collapse;">
            """
            for c in cuotas:
                html_content += f"""
                <tr>
                    <td>Cuota #{c.get('numero_cuota', 1)}</td>
                    <td>Vence: {c.get('fecha_vencimiento_cuota', '')}</td>
                    <td style="text-align:right; font-weight:bold;">{moneda_simbolo} {float(c.get('monto_cuota', 0.0)):.2f}</td>
                </tr>
                """
            html_content += "</table></div>"
        else:
            html_content += "<div></div>"
            
        html_content += f"""
            <div class="totales-box">
                <table class="totales-table">
                    <tr>
                        <td>Op. Gravada:</td>
                        <td style="text-align:right;">{moneda_simbolo} {subtotal:.2f}</td>
                    </tr>
                    {f"<tr><td>Descuento Total:</td><td style='text-align:right; color:#B00000;'>- {moneda_simbolo} {monto_descuento:.2f}</td></tr>" if monto_descuento > 0 else ""}
                    <tr>
                        <td>I.G.V. (18%):</td>
                        <td style="text-align:right;">{moneda_simbolo} {total_impuestos:.2f}</td>
                    </tr>
                    <tr class="total-row">
                        <td>Importe Total:</td>
                        <td style="text-align:right;">{moneda_simbolo} {total:.2f}</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="footer">
            Esta es una representación impresa de un comprobante electrónico regulado por SUNAT.<br>
            ¡Muchas gracias por su preferencia!
        </div>
    </div>
    
    <script>
        window.onload = function() {{
            window.print();
        }};
    </script>
</body>
</html>
"""

    # sanitizar caracteres no validos para nombres de archivo
    nombre_seguro = num_factura
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        nombre_seguro = nombre_seguro.replace(c, '_')
    file_path = os.path.join(IMPRESAS_DIR, f"factura_{nombre_seguro}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    webbrowser.open("file://" + os.path.abspath(file_path))
    return file_path


def generar_xml_ubl_sunat(factura_data):
    # genera un comprobante xml en formato ubl 2.1 estructurado
    num_factura = factura_data.get("num_factura", "F001-00000")
    partes = num_factura.split('-')
    serie = partes[0] if len(partes) > 0 else "F001"
    correlativo = partes[1] if len(partes) > 1 else "00000"
    
    fecha_emision = factura_data.get("fecha_emision", datetime.now().strftime("%Y-%m-%d"))
    empresa_nombre = factura_data.get("empresa_nombre", "UCSM S.A.")
    empresa_ruc = factura_data.get("empresa_ruc", "20102030401")
    
    cliente_nombre = factura_data.get("cliente_nombre", "Público General")
    cliente_doc = factura_data.get("dni_ruc", "00000000")
    cliente_tipo_doc = "6" if len(cliente_doc) == 11 else "1" # 6ruc 1dni
    
    moneda_iso = factura_data.get("moneda_iso", "PEN")
    subtotal = float(factura_data.get("subtotal", 0.0))
    total_impuestos = float(factura_data.get("total_impuestos", 0.0))
    total = float(factura_data.get("total", 0.0))
    
    # namespaces ubl estandar sunat
    root = ET.Element("Invoice", {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
        "xmlns:ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    })
    
    # cabecera basica
    cbc_id = ET.SubElement(root, "cbc:ID")
    cbc_id.text = num_factura
    
    cbc_issue_date = ET.SubElement(root, "cbc:IssueDate")
    cbc_issue_date.text = fecha_emision
    
    cbc_invoice_type = ET.SubElement(root, "cbc:InvoiceTypeCode", {"listID": "0101"})
    cbc_invoice_type.text = "01" if serie.startswith("F") else "03" # 01factura 03boleta
    
    cbc_currency = ET.SubElement(root, "cbc:DocumentCurrencyCode")
    cbc_currency.text = moneda_iso
    
    # emisor
    supplier = ET.SubElement(root, "cac:AccountingSupplierParty")
    supplier_party = ET.SubElement(supplier, "cac:Party")
    sup_tax = ET.SubElement(supplier_party, "cac:PartyTaxScheme")
    sup_tax_id = ET.SubElement(sup_tax, "cbc:RegistrationName")
    sup_tax_id.text = empresa_nombre
    sup_tax_company = ET.SubElement(sup_tax, "cbc:CompanyID")
    sup_tax_company.text = empresa_ruc
    
    # receptor
    customer = ET.SubElement(root, "cac:AccountingCustomerParty")
    customer_party = ET.SubElement(customer, "cac:Party")
    cust_tax = ET.SubElement(customer_party, "cac:PartyTaxScheme")
    cust_tax_id = ET.SubElement(cust_tax, "cbc:RegistrationName")
    cust_tax_id.text = cliente_nombre
    cust_tax_company = ET.SubElement(cust_tax, "cbc:CompanyID", {"schemeID": cliente_tipo_doc})
    cust_tax_company.text = cliente_doc
    
    # impuesto total
    tax_total = ET.SubElement(root, "cac:TaxTotal")
    tax_amount = ET.SubElement(tax_total, "cbc:TaxAmount", {"currencyID": moneda_iso})
    tax_amount.text = f"{total_impuestos:.2f}"
    
    # total monetario
    monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
    line_extension = ET.SubElement(monetary_total, "cbc:LineExtensionAmount", {"currencyID": moneda_iso})
    line_extension.text = f"{subtotal:.2f}"
    payable_amount = ET.SubElement(monetary_total, "cbc:PayableAmount", {"currencyID": moneda_iso})
    payable_amount.text = f"{total:.2f}"
    
    # lineas del detalle
    for idx, item in enumerate(factura_data.get("items", []), start=1):
        line = ET.SubElement(root, "cac:InvoiceLine")
        
        l_id = ET.SubElement(line, "cbc:ID")
        l_id.text = str(idx)
        
        qty = ET.SubElement(line, "cbc:InvoicedQuantity", {"unitCode": "NIU"})
        qty.text = str(item.get("cantidad", 1))
        
        line_extension_amount = ET.SubElement(line, "cbc:LineExtensionAmount", {"currencyID": moneda_iso})
        line_extension_subtotal = float(item.get("precio_unitario_historico", 0.0)) * float(item.get("cantidad", 1)) - float(item.get("monto_descuento_linea", 0.0))
        line_extension_amount.text = f"{line_extension_subtotal:.2f}"
        
        # item descripcion
        line_item = ET.SubElement(line, "cac:Item")
        item_desc = ET.SubElement(line_item, "cbc:Description")
        item_desc.text = item.get("producto_nombre", "Prod")
        
        # precio
        price = ET.SubElement(line, "cac:Price")
        price_amount = ET.SubElement(price, "cbc:PriceAmount", {"currencyID": moneda_iso})
        price_amount.text = f"{float(item.get('precio_unitario_historico', 0.0)):.2f}"
        
    xml_tree = ET.ElementTree(root)
    ET.indent(xml_tree, space="  ", level=0)
    
    xml_filename = f"{serie}-{correlativo}.xml"
    xml_path = os.path.join(XML_DIR, xml_filename)
    xml_tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return xml_path

def imprimir_asiento_html(num_factura, asientos, parent_widget=None):
    # Genera y abre en navegador un HTML estilizado para el asiento contable
    if not asientos:
        return None
        
    # Usar el primer asiento para el nombre de archivo
    num_asiento = asientos[0].get("num_asiento", "AC-00000")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Asiento Contable {num_asiento}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 40px;
            color: #1B2A4A;
            background-color: #F4F6F9;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #1B2A4A;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: #1B2A4A;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 30px;
            background-color: #F8FAFC;
            padding: 20px;
            border: 1px solid #E6E9ED;
            border-radius: 6px;
        }}
        .meta-item {{
            font-size: 13px;
        }}
        .meta-label {{
            font-weight: bold;
            color: #5A6580;
            text-transform: uppercase;
            font-size: 11px;
            margin-bottom: 4px;
        }}
        .meta-val {{
            font-weight: bold;
            color: #1B2A4A;
            font-size: 14px;
        }}
        .asiento-block {{
            margin-bottom: 40px;
        }}
        .asiento-title {{
            font-size: 16px;
            font-weight: bold;
            color: #1B2A4A;
            border-left: 4px solid #70AD47;
            padding-left: 10px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        th {{
            background-color: #1B2A4A;
            color: white;
            font-size: 12px;
            font-weight: bold;
            padding: 12px 10px;
            text-align: left;
            text-transform: uppercase;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #E6E9ED;
            font-size: 13px;
        }}
        tr:nth-child(even) {{
            background-color: #F8FAFC;
        }}
        .text-right {{
            text-align: right;
        }}
        .text-center {{
            text-align: center;
        }}
        .totales-row {{
            font-weight: bold;
        }}
        .totales-row td {{
            font-weight: bold;
            background-color: #EEF2FA;
            border-top: 2px solid #1B2A4A;
            font-size: 14px;
        }}
        .badge {{
            display: inline-block;
            color: #468847;
            font-size: 11px;
            font-weight: bold;
            background-color: #DFF0D8;
            border: 1px solid #D6E9C6;
            border-radius: 4px;
            padding: 4px 8px;
            text-transform: uppercase;
        }}
        .no-print {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .btn-print {{
            background-color: #70AD47;
            color: white;
            font-weight: bold;
            padding: 10px 24px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-print:hover {{
            background-color: #5B9337;
        }}
        @media print {{
            body {{
                background-color: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <button class="btn-print" onclick="window.print();">Imprimir Asiento Contable</button>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>Representación Física de Asiento Contable</h1>
        </div>
"""

    for as_data in asientos:
        total_debe = float(as_data.get("total_debe", 0.0))
        total_haber = float(as_data.get("total_haber", 0.0))
        glosa = html.escape(str(as_data.get("glosa", "")))
        fecha = as_data.get("fecha", "")
        num_as = as_data.get("num_asiento", "")
        
        html_content += f"""
        <div class="asiento-block">
            <div class="asiento-title">Asiento: {num_as}</div>
            
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Glosa General</div>
                    <div class="meta-val">{glosa}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Fecha de Registro</div>
                    <div class="meta-val">{fecha}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Documento de Referencia</div>
                    <div class="meta-val">Factura {num_factura}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Estado Contable</div>
                    <div class="meta-val"><span class="badge">CUADRADO</span></div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 15%;">Cuenta</th>
                        <th style="width: 55%;">Denominación / Descripción</th>
                        <th style="width: 15%; text-align: right;">Debe (S/)</th>
                        <th style="width: 15%; text-align: right;">Haber (S/)</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for line in as_data.get("detalles", []):
            code = html.escape(str(line.get("cuenta_codigo", "")))
            name = html.escape(str(line.get("cuenta_nombre", "")))
            debe = float(line.get("debe", 0.0))
            haber = float(line.get("haber", 0.0))
            
            debe_str = f"S/ {debe:,.2f}" if debe > 0 else "—"
            haber_str = f"S/ {haber:,.2f}" if haber > 0 else "—"
            
            html_content += f"""
                    <tr>
                        <td class="text-center"><b>{code}</b></td>
                        <td>{name}</td>
                        <td class="text-right">{debe_str}</td>
                        <td class="text-right">{haber_str}</td>
                    </tr>
            """
            
        html_content += f"""
                    <tr class="totales-row">
                        <td colspan="2" class="text-right">TOTALES:</td>
                        <td class="text-right">S/ {total_debe:,.2f}</td>
                        <td class="text-right">S/ {total_haber:,.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    html_content += """
    </div>
</body>
</html>
"""

    # Sanitizar nombre de archivo
    nombre_seguro = num_asiento
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        nombre_seguro = nombre_seguro.replace(c, '_')
        
    file_path = os.path.join(IMPRESAS_DIR, f"asiento_{nombre_seguro}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    webbrowser.open("file://" + os.path.abspath(file_path))
    return file_path
