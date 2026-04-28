#!/usr/bin/env python3
# server.py - NX PRO VAULT (Diseño Cyberpunk Profesional)

from flask import Flask, request, jsonify, send_file, abort
import os
import logging
import hashlib
import random
import string
import secrets
from datetime import datetime
import zipfile
from io import BytesIO
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

PRODUCTOS = {
    "prod_bundle_vj": {
        "nombre": "NX BUNDLE • 3 Visualizadores en Tiempo Real",
        "archivo": "bundle",
        "precio": 15.00,
        "tipo": "bundle",
        "descripcion": "Incluye: KALEIDO + GRID | ASCII WEBCAM FLAME | VJ GLITCH ENGINE"
    },
    "sub_pro_mensual": {
        "nombre": "SUSCRIPCIÓN NX PRO",
        "archivo": "subscription",
        "precio": 7.00,
        "tipo": "suscripcion",
        "descripcion": "Acceso a todos los visuales + 3 nuevos cada mes"
    }
}

descargas_autorizadas = {}
suscripciones_activas = {}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def generar_contrasena(email_cliente):
    base = f"{email_cliente}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:8].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NX-{hash_str}{extras}"

def verificar_suscripcion(token):
    if token not in suscripciones_activas:
        return None
    suscripcion = suscripciones_activas[token]
    if datetime.now().timestamp() > suscripcion["expira"]:
        return None
    return suscripcion

def obtener_temporadas():
    seasons = []
    try:
        if not os.path.exists("files"):
            os.makedirs("files", exist_ok=True)
        
        season_dirs = sorted(glob.glob("files/season_*"))
        for season_dir in season_dirs:
            season_name = os.path.basename(season_dir)
            visuales = []
            for html_file in sorted(glob.glob(f"{season_dir}/*.html")):
                filename = os.path.basename(html_file)
                friendly_name = filename.replace('.html', '').replace('_', ' ').title()
                visuales.append({
                    "archivo": filename,
                    "nombre": friendly_name,
                    "ruta": f"/visual/{season_name}/{filename}"
                })
            if visuales:
                season_num = season_name.replace('season_', '')
                seasons.append({
                    "id": season_name,
                    "nombre": f"TEMPORADA {season_num}",
                    "numero": int(season_num),
                    "visuales": visuales
                })
    except Exception as e:
        logger.error(f"Error obteniendo temporadas: {e}")
    
    return sorted(seasons, key=lambda x: x["numero"]) if seasons else []

def crear_zip_bundle():
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        archivos = [
            ("files/season_01/kaleido.html", "01_NX_KALEIDO_ENGINE.html"),
            ("files/season_01/ascii.html", "02_NX_ASCII_ENGINE.html"),
            ("files/season_01/glitch.html", "03_NX_GLITCH_ENGINE.html")
        ]
        for origen, destino in archivos:
            if os.path.exists(origen):
                zf.write(origen, destino)
        
        manual_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>NX ENGINES - Manual de Usuario</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Space Grotesk', sans-serif;
                    background: #0a0a0a;
                    color: #e0e0e0;
                    line-height: 1.6;
                }
                .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
                .hero { text-align: center; margin-bottom: 50px; }
                .hero h1 { font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, #8b5cf6, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
                .hero p { color: #888; font-size: 1.1rem; }
                .card { background: #111; border-radius: 16px; padding: 30px; margin-bottom: 30px; border: 1px solid #222; }
                .card h2 { color: #8b5cf6; margin-bottom: 20px; font-size: 1.5rem; }
                .card h3 { color: #00c853; margin: 20px 0 10px; font-size: 1.2rem; }
                .key { background: #1a1a1a; padding: 4px 10px; border-radius: 6px; font-family: monospace; color: #ffaa44; border: 1px solid #333; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                td, th { padding: 12px; border-bottom: 1px solid #222; text-align: left; }
                .footer { text-align: center; margin-top: 50px; padding-top: 30px; border-top: 1px solid #222; color: #555; font-size: 0.8rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="hero">
                    <h1>NX ENGINES</h1>
                    <p>Manual de Usuario · Visuales en Tiempo Real</p>
                </div>
                <div class="card">
                    <h2>🎬 Bienvenido</h2>
                    <p>Gracias por adquirir el bundle NX ENGINES. Este manual te guiará para sacar el máximo provecho de tus visualizadores.</p>
                </div>
                <div class="card">
                    <h2>📦 Contenido del Bundle</h2>
                    <ul>
                        <li><strong>🌀 NX KALEIDO ENGINE</strong> - Efectos kaleidoscopio + grid VHS + glow</li>
                        <li><strong>🔥 NX ASCII ENGINE</strong> - ASCII art + webcam mix + partículas de fuego</li>
                        <li><strong>🎛️ NX GLITCH ENGINE</strong> - 5 figuras 3D + shaders + glitch/delay/echo</li>
                    </ul>
                </div>
                <div class="card">
                    <h2>🚀 Inicio Rápido</h2>
                    <ol>
                        <li>Abre cualquier archivo <strong>.html</strong> en tu navegador (Chrome, Firefox, Edge)</li>
                        <li>Permite el acceso al <strong>micrófono</strong> cuando el navegador lo solicite</li>
                        <li>Conecta tu música (por altavoces o línea de audio)</li>
                        <li>¡Disfruta de los visuales sincronizados con el audio!</li>
                    </ol>
                </div>
                <div class="card">
                    <h2>🎛️ Controles Generales</h2>
                    <table>
                        <tr><th>Tecla</th><th>Función</th></tr>
                        <tr><td><span class="key">TAB</span></td><td>Ocultar/Mostrar interfaz</td></tr>
                        <tr><td><span class="key">P</span></td><td>Activar/Desactivar micrófono</td></tr>
                        <tr><td><span class="key">O</span></td><td>Cambiar banda de audio</td></tr>
                        <tr><td><span class="key">+ / -</span></td><td>Ajustar intensidad</td></tr>
                        <tr><td><span class="key">T</span></td><td>Capturar pantalla (PNG)</td></tr>
                        <tr><td><span class="key">Y</span></td><td>Grabar video (WEBM)</td></tr>
                    </table>
                </div>
                <div class="card">
                    <h2>💬 Soporte</h2>
                    <p>📧 <strong>soporte@najarrox.xyz</strong></p>
                    <p>🌐 <strong>www.najarrox.xyz</strong></p>
                </div>
                <div class="footer">
                    <p>© 2026 NAJARRO X STUDIO · Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        zf.writestr("00_MANUAL_NX_ENGINES.html", manual_html)
        
        readme = """========================================
   NAJARRO X STUDIO - NX ENGINES
========================================

🎬 ¡GRACIAS POR TU COMPRA!

Este bundle incluye 3 visualizadores en tiempo real.

📖 MANUAL: Abre "00_MANUAL_NX_ENGINES.html" para instrucciones.

Para soporte: soporte@najarrox.xyz
Web: www.najarrox.xyz

© 2026 NAJARRO X STUDIO
"""
        zf.writestr("README.txt", readme)
    
    memory_file.seek(0)
    return memory_file

def enviar_email_simple(destinatario, nombre, asunto, cuerpo_html):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    GMAIL_USER = os.environ.get('GMAIL_USER', 'najarrox.exe@gmail.com')
    GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', 'obpg ctik ngcn ipqf')
    
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Email enviado a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"❌ Error email: {e}")
        return False

# ============================================
# WEBHOOK
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error"}), 400
        
        event_type = data.get('event_type')
        logger.info(f"📨 Evento: {event_type}")
        
        if event_type == 'payment_intent.succeeded':
            producto_id = data.get('product', {}).get('id')
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            
            if not producto_id or not email:
                return jsonify({"status": "error"}), 400
            
            if producto_id not in PRODUCTOS:
                logger.warning(f"Producto desconocido: {producto_id}")
                return jsonify({"status": "ignored"}), 200
            
            producto = PRODUCTOS[producto_id]
            token = secrets.token_urlsafe(32)
            contrasena = generar_contrasena(email)
            
            descargas_autorizadas[email] = {
                "contrasena": contrasena,
                "timestamp": datetime.now().timestamp(),
                "nombre": nombre,
                "producto_id": producto_id,
                "token": token
            }
            
            link_descarga = f"https://{request.host}/descargar/{token}"
            
            html_email = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
                    body {{ font-family: 'Space Grotesk', sans-serif; background: #0a0a0a; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #111; border: 1px solid #222; border-radius: 16px; padding: 40px; }}
                    h1 {{ background: linear-gradient(135deg, #8b5cf6, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8rem; }}
                    .box {{ background: #0a0a0a; padding: 20px; border-radius: 12px; margin: 20px 0; }}
                    .btn {{ display: inline-block; background: #8b5cf6; color: black; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
                    .footer {{ font-size: 11px; color: #555; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎬 ¡Gracias por tu compra, {nombre}!</h1>
                    <p><strong>{producto['nombre']}</strong></p>
                    <p>{producto['descripcion']}</p>
                    <div class="box">
                        <p>🔗 <strong>TU ENLACE DE DESCARGA:</strong></p>
                        <a href="{link_descarga}" style="color:#8b5cf6;">{link_descarga}</a>
                        <p style="margin-top:15px;">🔐 <strong>CONTRASEÑA:</strong> {contrasena}</p>
                    </div>
                    <a href="{link_descarga}" class="btn">📦 DESCARGAR BUNDLE</a>
                    <div class="footer">
                        <p>Enlace válido por 7 días · NAJARRO X STUDIO</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, f"Tu {producto['nombre']} está listo", html_email)
            logger.info(f"✅ Venta completada: {producto_id} -> {email}")
            return jsonify({"status": "ok"}), 200
        
        elif event_type == 'subscription.active':
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            
            if not email:
                return jsonify({"status": "error"}), 400
            
            token_sub = secrets.token_urlsafe(32)
            fecha_expiracion = datetime.now().timestamp() + 30 * 24 * 3600
            
            suscripciones_activas[token_sub] = {
                "email": email,
                "nombre": nombre,
                "expira": fecha_expiracion,
                "activa": True
            }
            
            link_vault = f"https://{request.host}/vault?token={token_sub}"
            
            html_email = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
                    body {{ font-family: 'Space Grotesk', sans-serif; background: #0a0a0a; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #111; border: 1px solid #222; border-radius: 16px; padding: 40px; }}
                    h1 {{ background: linear-gradient(135deg, #8b5cf6, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .box {{ background: #0a0a0a; padding: 20px; border-radius: 12px; margin: 20px 0; }}
                    .btn {{ display: inline-block; background: #8b5cf6; color: black; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎬 ¡Bienvenido a NX PRO, {nombre}!</h1>
                    <p>Tu suscripción está activa.</p>
                    <div class="box">
                        <p>🔗 <strong>TU VAULT PERSONAL:</strong></p>
                        <a href="{link_vault}" style="color:#8b5cf6;">{link_vault}</a>
                    </div>
                    <a href="{link_vault}" class="btn">🎨 ENTRAR AL VAULT</a>
                    <p style="margin-top:20px; font-size:11px; color:#555;">Guarda este enlace · Se renueva automáticamente</p>
                </div>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, "NX PRO - Tu suscripción está activa", html_email)
            logger.info(f"✅ Suscripción activada para {email}")
            return jsonify({"status": "ok", "token": token_sub}), 200
        
        elif event_type == 'subscription.canceled':
            email = data.get('customer', {}).get('email')
            for token, sub in suscripciones_activas.items():
                if sub["email"] == email:
                    suscripciones_activas[token]["activa"] = False
                    logger.info(f"❌ Suscripción cancelada para {email}")
                    break
            return jsonify({"status": "ok"}), 200
        
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# ENDPOINTS
# ============================================

@app.route('/descargar/<token>')
def descargar_archivo(token):
    email = None
    datos = None
    for mail, d in descargas_autorizadas.items():
        if d.get("token") == token:
            email = mail
            datos = d
            break
    
    if not datos:
        return "Enlace inválido", 404
    
    if datetime.now().timestamp() - datos["timestamp"] > 7 * 24 * 3600:
        return "Enlace expirado", 403
    
    return send_file(
        crear_zip_bundle(), 
        as_attachment=True, 
        download_name=f"NX_BUNDLE_{datetime.now().strftime('%Y%m%d')}.zip", 
        mimetype="application/zip"
    )

@app.route('/verificar-suscripcion')
def verificar_suscripcion_endpoint():
    token = request.args.get('token')
    if not token:
        return jsonify({"activa": False, "error": "Token requerido"}), 400
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return jsonify({"activa": False, "error": "Token inválido"}), 200
    
    return jsonify({
        "activa": True,
        "expira": suscripcion["expira"],
        "email": suscripcion["email"],
        "nombre": suscripcion["nombre"]
    })

# ============================================
# VAULT CON DISEÑO PROFESIONAL
# ============================================

@app.route('/vault')
def vault_suscriptor():
    token = request.args.get('token')
    if not token:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Acceso Pro • Najarro X</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { background: #0a0a0a; font-family: 'Space Grotesk', sans-serif; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
                .card { background: #111; border-radius: 24px; padding: 50px; text-align: center; border: 1px solid #222; max-width: 500px; }
                h1 { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #8b5cf6, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
                .btn { background: #8b5cf6; color: black; padding: 12px 30px; text-decoration: none; border-radius: 40px; font-weight: 600; display: inline-block; margin-top: 20px; }
                p { color: #888; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🔐 ACCESO PRO</h1>
                <p>Este contenido es exclusivo para suscriptores de NX PRO.</p>
                <a href="https://www.najarrox.xyz" class="btn">SUSCRIBIRME</a>
            </div>
        </body>
        </html>
        ''', 403
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return "Suscripción expirada", 403
    
    seasons = obtener_temporadas()
    fecha_expiracion = datetime.fromtimestamp(suscripcion["expira"]).strftime('%d/%m/%Y')
    
    # Verificar si existe la imagen del logo
    logo_path = "/files/images/logo.png"
    logo_html = f'<img src="{logo_path}" alt="Najarro X" style="height: 50px; width: auto;">' if os.path.exists("files/images/logo.png") else '<h1 style="font-size: 1.5rem;">NX PRO VAULT</h1>'
    
    html = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NX PRO VAULT • {suscripcion["nombre"]}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                background: #0a0a0a;
                font-family: 'Space Grotesk', sans-serif;
                color: #fff;
            }}
            
            /* HEADER CYBERPUNK */
            .header {{
                background: linear-gradient(135deg, #0a0a0a 0%, #111 100%);
                border-bottom: 1px solid #222;
                padding: 20px 30px;
                position: sticky;
                top: 0;
                z-index: 100;
                backdrop-filter: blur(10px);
            }}
            
            .header-container {{
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                    justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
            }}
            
            .logo-area {{
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            
            .logo-area h1 {{
                font-family: 'Space Grotesk', monospace;
                font-weight: 700;
                font-size: 1.5rem;
                letter-spacing: -0.02em;
                background: linear-gradient(135deg, #fff 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .logo-area p {{
                font-size: 0.75rem;
                color: #888;
                letter-spacing: 2px;
            }}
            
            .user-info {{
                text-align: right;
            }}
            
            .user-info .name {{
                font-weight: 600;
                color: #8b5cf6;
            }}
            
            .user-info .expiry {{
                font-size: 0.7rem;
                color: #00c853;
            }}
            
            .badge {{
                background: rgba(0, 200, 83, 0.15);
                border: 1px solid #00c853;
                color: #00c853;
                padding: 4px 12px;
                border-radius: 40px;
                font-size: 0.7rem;
                font-weight: 500;
            }}
            
            /* MAIN CONTENT */
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px 30px;
            }}
            
            /* STATS CARDS */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 50px;
            }}
            
            .stat-card {{
                background: #111;
                border: 1px solid #222;
                border-radius: 16px;
                padding: 20px;
                transition: all 0.3s ease;
            }}
            
            .stat-card:hover {{
                border-color: #8b5cf6;
                transform: translateY(-2px);
            }}
            
            .stat-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #8b5cf6;
            }}
            
            .stat-label {{
                font-size: 0.75rem;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 8px;
            }}
            
            /* SEASONS */
            .season {{
                margin-bottom: 60px;
            }}
            
            .season-title {{
                font-size: 1.8rem;
                font-weight: 600;
                margin-bottom: 25px;
                display: inline-block;
                background: linear-gradient(135deg, #fff, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                border-left: 4px solid #8b5cf6;
                padding-left: 20px;
            }}
            
            /* GRID DE VISUALES */
            .visual-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 25px;
            }}
            
            .visual-card {{
                background: #111;
                border: 1px solid #222;
                border-radius: 20px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            }}
            
            .visual-card:hover {{
                transform: translateY(-8px);
                border-color: #8b5cf6;
                box-shadow: 0 20px 40px rgba(139, 92, 246, 0.15);
            }}
            
            .visual-preview {{
                height: 200px;
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 64px;
                position: relative;
            }}
            
            .visual-preview::after {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.5) 100%);
                pointer-events: none;
            }}
            
            .visual-info {{
                padding: 20px;
            }}
            
            .visual-info h3 {{
                font-size: 1.2rem;
                font-weight: 600;
                color: #fff;
                margin-bottom: 8px;
            }}
            
            .visual-info p {{
                font-size: 0.8rem;
                color: #888;
                margin-bottom: 15px;
                font-family: 'Space Grotesk', sans-serif;
            }}
            
            .btn-open {{
                background: transparent;
                border: 1.5px solid #8b5cf6;
                color: #8b5cf6;
                padding: 8px 20px;
                border-radius: 40px;
                font-size: 0.75rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: 'Space Grotesk', sans-serif;
            }}
            
            .btn-open:hover {{
                background: #8b5cf6;
                color: #000;
            }}
            
            /* FOOTER */
            .footer {{
                text-align: center;
                padding: 40px 30px;
                border-top: 1px solid #222;
                margin-top: 40px;
            }}
            
            .footer p {{
                color: #555;
                font-size: 0.7rem;
                letter-spacing: 1px;
            }}
            
            .footer a {{
                color: #8b5cf6;
                text-decoration: none;
            }}
            
            @media (max-width: 768px) {{
                .header-container {{
                    flex-direction: column;
                    text-align: center;
                }}
                .user-info {{
                    text-align: center;
                }}
                .season-title {{
                    font-size: 1.3rem;
                }}
                .visual-grid {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-container">
                <div class="logo-area">
                    {logo_html}
                    <div>
                        <h1>NAJARRO X VJ LIVE</h1>
                        <p>REAL-TIME VISUAL ENGINE</p>
                    </div>
                </div>
                <div class="user-info">
                    <div class="name">{suscripcion["nombre"]}</div>
                    <div class="expiry">Activo hasta {fecha_expiracion}</div>
                    <div class="badge" style="margin-top: 8px;">✅ PRO ACTIVO</div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{sum(len(s["visuales"]) for s in seasons)}</div>
                    <div class="stat-label">VISUALES DISPONIBLES</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(seasons)}</div>
                    <div class="stat-label">TEMPORADAS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">+3</div>
                    <div class="stat-label">NUEVOS / MES</div>
                </div>
            </div>
    '''
    
    for season in seasons:
        html += f'''
            <div class="season">
                <div class="season-title">📀 {season["nombre"]}</div>
                <div class="visual-grid">
        '''
        for visual in season["visuales"]:
            emoji = "🌀" if "kaleido" in visual["archivo"].lower() else "🔥" if "ascii" in visual["archivo"].lower() else "🎛️" if "glitch" in visual["archivo"].lower() else "✨"
            visual_url = f"{visual['ruta']}?token={token}"
            html += f'''
                    <div class="visual-card" onclick="window.open('{visual_url}', '_blank')">
                        <div class="visual-preview">{emoji}</div>
                        <div class="visual-info">
                            <h3>{visual["nombre"]}</h3>
                            <p>Visual en tiempo real • Audio-reactivo • 60FPS</p>
                            <button class="btn-open">🎬 ABRIR VISUALIZADOR</button>
                        </div>
                    </div>
            '''
        html += '''
                </div>
            </div>
        '''
    
    html += '''
            <div class="footer">
                <p>🔒 VISUALES EXCLUSIVOS PARA SUSCRIPTORES NX PRO</p>
                <p>© 2026 <a href="https://www.najarrox.xyz">NAJARRO X STUDIO</a> · PANAMÁ · soporte@najarrox.xyz</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

# ============================================
# SERVIDOR DE VISUALES Y DEMO
# ============================================

@app.route('/visual/<season>/<filename>')
def servir_visual(season, filename):
    token = request.args.get('token')
    
    if token:
        suscripcion = verificar_suscripcion(token)
        if not suscripcion:
            return "Suscripción inválida o expirada", 403
        modo_suscriptor = True
    else:
        modo_suscriptor = False
    
    ruta = os.path.join("files", season, filename)
    if not os.path.exists(ruta):
        return "Visual no encontrado", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    if not modo_suscriptor:
        demo_script = '''
        <div id="nx-demo-badge" style="position:fixed;bottom:20px;right:20px;background:rgba(0,0,0,0.95);color:#ffaa44;font-family:'Space Grotesk',monospace;padding:12px 20px;z-index:9999;font-size:14px;font-weight:600;border-right:3px solid #ffaa44;border-radius:12px 0 0 12px;backdrop-filter:blur(12px);pointer-events:none;letter-spacing:1px;">
            🎬 DEMO | 2:00
        </div>
        <script>
            (function() {
                let tiempo = 120;
                let bloqueado = false;
                const badge = document.getElementById('nx-demo-badge');
                if(!badge) return;
                
                function bloquearPantalla() {
                    if(bloqueado) return;
                    bloqueado = true;
                    
                    const blocker = document.createElement('div');
                    blocker.id = 'nx-blocker';
                    blocker.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.98);z-index:100000;display:flex;justify-content:center;align-items:center;font-family:\'Space Grotesk\',sans-serif;text-align:center;backdrop-filter:blur(10px);';
                    blocker.innerHTML = `
                        <div style="background:#111;padding:50px;border:2px solid #ff4444;border-radius:24px;max-width:500px;">
                            <div style="font-size:64px;">⏰</div>
                            <h1 style="color:#ff4444;font-size:2rem;margin:20px 0;">DEMO EXPIRADA</h1>
                            <p style="color:#ccc;margin-bottom:30px;">El tiempo de prueba de 2 minutos ha terminado.</p>
                            <p style="color:#8b5cf6;margin-bottom:20px;">Adquiere el bundle completo por solo $15</p>
                            <a href="https://nxvjweb.onrender.com/" style="background:#8b5cf6;color:black;padding:14px 28px;text-decoration:none;font-weight:700;border-radius:40px;display:inline-block;">🛒 COMPRAR AHORA</a>
                            <p style="margin-top:30px;font-size:11px;color:#555;">www.najarrox.xyz</p>
                        </div>
                    `;
                    document.body.appendChild(blocker);
                }
                
                const interval = setInterval(function() {
                    if(bloqueado) return;
                    tiempo--;
                    var mins = Math.floor(tiempo/60);
                    var segs = (tiempo%60).toString().padStart(2,'0');
                    if(badge) badge.innerHTML = '🎬 DEMO | ' + mins + ':' + segs;
                    
                    if(tiempo <= 10 && tiempo > 0) {
                        badge.style.borderRightColor = '#ff4444';
                        badge.style.backgroundColor = 'rgba(0,0,0,0.98)';
                    }
                    
                    if(tiempo <= 0) {
                        clearInterval(interval);
                        bloquearPantalla();
                    }
                }, 1000);
            })();
        </script>
        '''
        contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/demo/kaleido')
def demo_kaleido():
    ruta = os.path.join("files", "season_01", "kaleido.html")
    if not os.path.exists(ruta):
        return "Demo no disponible", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    demo_script = '''
    <div id="nx-demo-badge" style="position:fixed;bottom:20px;right:20px;background:rgba(0,0,0,0.95);color:#ffaa44;font-family:'Space Grotesk',monospace;padding:12px 20px;z-index:9999;font-size:14px;font-weight:600;border-right:3px solid #ffaa44;border-radius:12px 0 0 12px;backdrop-filter:blur(12px);pointer-events:none;letter-spacing:1px;">
        🎬 DEMO | 2:00
    </div>
    <script>
        (function() {
            let tiempo = 120;
            let bloqueado = false;
            const badge = document.getElementById('nx-demo-badge');
            if(!badge) return;
            
            function bloquearPantalla() {
                if(bloqueado) return;
                bloqueado = true;
                
                const blocker = document.createElement('div');
                blocker.id = 'nx-blocker';
                blocker.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.98);z-index:100000;display:flex;justify-content:center;align-items:center;font-family:\'Space Grotesk\',sans-serif;text-align:center;backdrop-filter:blur(10px);';
                blocker.innerHTML = `
                    <div style="background:#111;padding:50px;border:2px solid #ff4444;border-radius:24px;max-width:500px;">
                        <div style="font-size:64px;">⏰</div>
                        <h1 style="color:#ff4444;font-size:2rem;margin:20px 0;">DEMO EXPIRADA</h1>
                        <p style="color:#ccc;margin-bottom:30px;">El tiempo de prueba de 2 minutos ha terminado.</p>
                        <p style="color:#8b5cf6;margin-bottom:20px;">Adquiere el bundle completo por solo $15</p>
                        <a href="https://nxvjweb.onrender.com/" style="background:#8b5cf6;color:black;padding:14px 28px;text-decoration:none;font-weight:700;border-radius:40px;display:inline-block;">🛒 COMPRAR AHORA</a>
                        <p style="margin-top:30px;font-size:11px;color:#555;">www.najarrox.xyz</p>
                    </div>
                `;
                document.body.appendChild(blocker);
            }
            
            const interval = setInterval(function() {
                if(bloqueado) return;
                tiempo--;
                var mins = Math.floor(tiempo/60);
                var segs = (tiempo%60).toString().padStart(2,'0');
                if(badge) badge.innerHTML = '🎬 DEMO | ' + mins + ':' + segs;
                
                if(tiempo <= 10 && tiempo > 0) {
                    badge.style.borderRightColor = '#ff4444';
                    badge.style.backgroundColor = 'rgba(0,0,0,0.98)';
                }
                
                if(tiempo <= 0) {
                    clearInterval(interval);
                    bloquearPantalla();
                }
            }, 1000);
        })();
    </script>
    '''
    contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/files/images/<path:filename>')
def servir_imagen(filename):
    """Sirve imágenes desde la carpeta files/images/"""
    ruta = os.path.join("files", "images", filename)
    if not os.path.exists(ruta):
        return "Imagen no encontrada", 404
    return send_file(ruta, mimetype='image/png')

# ============================================
# PÁGINA PRINCIPAL
# ============================================

@app.route('/')
def home():
    seasons = obtener_temporadas()
    total_visuales = sum(len(s["visuales"]) for s in seasons)
    
    logo_html = '<img src="/files/images/logo.png" alt="Najarro X" style="height: 48px; width: auto;">' if os.path.exists("files/images/logo.png") else '<h1 style="font-size: 1.8rem;">NX</h1>'
    
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NAJARRO X • VJ LIVE ENGINES</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                background: #0a0a0a;
                font-family: 'Space Grotesk', sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            /* HERO SECTION */
            .hero {{
                text-align: center;
                margin-bottom: 60px;
            }}
            
            .logo {{
                margin-bottom: 20px;
            }}
            
            .hero h1 {{
                font-size: 3.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                background: linear-gradient(135deg, #fff 0%, #8b5cf6 40%, #00c853 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 15px;
            }}
            
            .hero p {{
                font-size: 1.1rem;
                color: #888;
                max-width: 600px;
                margin: 0 auto;
            }}
            
            .badge {{
                display: inline-block;
                background: rgba(139, 92, 246, 0.15);
                border: 1px solid #8b5cf6;
                color: #8b5cf6;
                padding: 6px 16px;
                border-radius: 40px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-top: 20px;
            }}
            
            /* CARDS */
            .cards-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 30px;
                margin-bottom: 50px;
            }}
            
            .card {{
                background: #111;
                border: 1px solid #222;
                border-radius: 24px;
                padding: 40px 30px;
                text-align: center;
                transition: all 0.3s ease;
            }}
            
            .card:hover {{
                transform: translateY(-5px);
                border-color: #8b5cf6;
                box-shadow: 0 20px 40px rgba(139, 92, 246, 0.1);
            }}
            
            .card-icon {{
                font-size: 48px;
                margin-bottom: 20px;
            }}
            
            .card h2 {{
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 10px;
                color: #fff;
            }}
            
            .card .price {{
                font-size: 2rem;
                font-weight: 700;
                color: #00c853;
                margin: 15px 0;
            }}
            
            .card .description {{
                color: #888;
                font-size: 0.85rem;
                margin-bottom: 25px;
            }}
            
            .btn-primary {{
                display: inline-block;
                background: #8b5cf6;
                color: #000;
                padding: 12px 28px;
                border-radius: 40px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.85rem;
                transition: all 0.2s ease;
                margin: 5px;
            }}
            
            .btn-primary:hover {{
                background: #a078f8;
                transform: scale(1.02);
            }}
            
            .btn-secondary {{
                display: inline-block;
                background: transparent;
                border: 1.5px solid #8b5cf6;
                color: #8b5cf6;
                padding: 12px 28px;
                border-radius: 40px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.85rem;
                transition: all 0.2s ease;
                margin: 5px;
            }}
            
            .btn-secondary:hover {{
                background: rgba(139, 92, 246, 0.1);
            }}
            
            .features {{
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
                margin-top: 30px;
            }}
            
            .feature {{
                text-align: center;
                font-size: 0.8rem;
                color: #666;
            }}
            
            .feature span {{
                display: block;
                font-size: 1.2rem;
                margin-bottom: 5px;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 60px;
                padding-top: 30px;
                border-top: 1px solid #222;
                color: #555;
                font-size: 0.7rem;
            }}
            
            .footer a {{
                color: #8b5cf6;
                text-decoration: none;
            }}
            
            @media (max-width: 768px) {{
                .hero h1 {{
                    font-size: 2rem;
                }}
                .cards-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <div class="logo">{logo_html}</div>
                <h1>NAJARRO X<br>VJ LIVE ENGINES</h1>
                <p>Visuales en tiempo real · Audio-reactivos · 60FPS</p>
                <div class="badge">⚡ REAL-TIME VISUAL SYNTHESIS ⚡</div>
            </div>
            
            <div class="cards-grid">
                <div class="card">
                    <div class="card-icon">🎬</div>
                    <h2>NX BUNDLE</h2>
                    <div class="price">$15 <span style="font-size: 0.9rem;">USD</span></div>
                    <p class="description">3 visualizadores profesionales</p>
                    <a href="/demo/kaleido" class="btn-secondary">🎨 PROBAR DEMO</a>
                    <a href="#" class="btn-primary" onclick="alert('Próximamente en Recurrente')">🛒 COMPRAR</a>
                </div>
                
                <div class="card">
                    <div class="card-icon">⭐</div>
                    <h2>NX PRO</h2>
                    <div class="price">$7 <span style="font-size: 0.9rem;">/mes</span></div>
                    <p class="description">Acceso ilimitado + contenido mensual</p>
                    <a href="https://recurrente.com/p/sub_pro_mensual" class="btn-primary">🎯 SUSCRIBIRME</a>
                </div>
            </div>
            
            <div class="features">
                <div class="feature"><span>🌀</span> Audio-reactivo</div>
                <div class="feature"><span>🎨</span> 3 visualizadores</div>
                <div class="feature"><span>📈</span> +3 nuevos/mes</div>
                <div class="feature"><span>⚡</span> 60 FPS</div>
            </div>
            
            <div class="footer">
                <p>© 2026 <a href="https://www.najarrox.xyz">NAJARRO X STUDIO</a> · Panamá · <a href="mailto:soporte@najarrox.xyz">soporte@najarrox.xyz</a></p>
                <p style="margin-top: 8px;">🔒 Descargas protegidas · Tokens únicos por compra</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "temporadas": len(obtener_temporadas()),
        "suscriptores_activos": len(suscripciones_activas),
        "descargas_unicas": len(descargas_autorizadas),
        "precio_bundle": 15.00,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 NX PRO VAULT iniciado en puerto {port}")
    logger.info(f"💰 Bundle: $15.00 | Suscripción: $7/mes")
    app.run(host='0.0.0.0', port=port, debug=False)