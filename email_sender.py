#!/usr/bin/env python3
# email_sender.py - Envío de emails para NX PRO VAULT

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GMAIL_USER = os.environ.get('GMAIL_USER', 'najarrox.exe@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', 'obpg ctik ngcn ipqf')

def enviar_email(destinatario, nombre_cliente, contrasena, link_descarga, producto, html_personalizado=None):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.error("❌ Credenciales no configuradas")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = f"🎬 NAJARRO X - Tu {producto['nombre']} está listo"
    
    if html_personalizado:
        html = html_personalizado
    else:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: 'Courier New', monospace; background: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border: 3px solid #000; padding: 30px;">
                <h1>🎬 ¡Gracias por tu compra, {nombre_cliente}!</h1>
                <p><strong>{producto['nombre']}</strong> - {producto['descripcion']}</p>
                <div style="background: #0a0a0a; color: white; padding: 20px; margin: 20px 0;">
                    <p>🔗 <strong>TU ENLACE DE DESCARGA:</strong></p>
                    <a href="{link_descarga}" style="color: #8b5cf6;">{link_descarga}</a>
                    <p style="margin-top: 15px;">🔐 <strong>CONTRASEÑA:</strong> {contrasena}</p>
                </div>
                <a href="{link_descarga}" style="display: inline-block; background: #8b5cf6; color: black; padding: 12px 24px; text-decoration: none; font-weight: bold;">📦 DESCARGAR</a>
                <div style="margin-top: 20px; font-size: 11px; color: #666;">
                    ⚠️ Enlace válido por 7 días.<br>
                    NAJARRO X STUDIO · soporte@najarrox.xyz
                </div>
            </div>
        </body>
        </html>
        """
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Email enviado a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False