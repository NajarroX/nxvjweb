#!/usr/bin/env python3
# email_sender.py - Envía emails con el link de descarga personalizado

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN (LEER DE VARIABLES DE ENTORNO)
# ============================================

GMAIL_USER = os.environ.get('GMAIL_USER', 'najarrox.exe@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', 'obpg ctik ngcn ipqf')

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def enviar_email(destinatario, nombre_cliente, contrasena, link_descarga, producto, html_personalizado=None):
    """
    Envía email con link de descarga protegido y contraseña
    """
    
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.error("❌ Credenciales de Gmail no configuradas")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = f"🎬 NAJARRO X - Tu {producto['nombre']} ya está listo"
    
    # Si hay HTML personalizado (como para suscripciones), usarlo
    if html_personalizado:
        html = html_personalizado
    else:
        # HTML estándar para productos normales
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Courier New', monospace; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border: 3px solid #000; padding: 30px; box-shadow: 8px 8px 0 #000; }}
                h1 {{ font-size: 1.8rem; border-left: 8px solid #8b5cf6; padding-left: 20px; }}
                .link-box {{ background: #0a0a0a; color: white; padding: 20px; margin: 20px 0; word-break: break-all; }}
                .password {{ font-size: 1.8rem; font-weight: bold; color: #00c853; }}
                .btn {{ display: inline-block; background: #8b5cf6; color: black; padding: 12px 24px; text-decoration: none; font-weight: bold; margin: 15px 0; }}
                .footer {{ font-size: 0.7rem; color: #666; margin-top: 20px; border-top: 1px solid #ddd; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎬 ¡Gracias por tu compra, {nombre_cliente}!</h1>
                <p><strong>{producto['nombre']}</strong> - {producto['descripcion']}</p>
                
                <div class="link-box">
                    <p>🔗 <strong>TU ENLACE DE DESCARGA PERSONAL:</strong></p>
                    <a href="{link_descarga}" style="color: #8b5cf6; word-break: break-all;">{link_descarga}</a>
                    
                    <p style="margin-top: 15px;">🔐 <strong>CONTRASEÑA (si es solicitada):</strong></p>
                    <p class="password">{contrasena}</p>
                </div>
                
                <a href="{link_descarga}" class="btn">📦 DESCARGAR AHORA</a>
                
                <div style="background: #f0f0f0; padding: 15px; margin: 20px 0;">
                    <p><strong>📖 INSTRUCCIONES:</strong></p>
                    <p>1. Haz clic en el botón o en el enlace de arriba</p>
                    <p>2. El archivo se descargará automáticamente</p>
                    <p>3. Abre el archivo .html en tu navegador (Chrome, Firefox, Edge)</p>
                    <p>4. Permite el acceso al micrófono cuando lo solicite</p>
                    <p>5. ¡Conecta tu música y disfruta los visuales en tiempo real!</p>
                </div>
                
                <div class="footer">
                    ⚠️ Este enlace es personal e intransferible.<br>
                    Expira en <strong>7 días</strong> desde la fecha de compra.<br>
                    Para soporte: <a href="mailto:soporte@najarrox.xyz">soporte@najarrox.xyz</a><br><br>
                    NAJARRO X ESTUDIO · Panamá · 2026
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
        logger.info(f"✅ Email enviado a {destinatario} - Producto: {producto['nombre']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email: {e}")
        return False