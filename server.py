#!/usr/bin/env python3
# server.py - NX PRO VAULT (Diseño con precios y features GIGANTES)

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

# ⏱️ TIEMPO DE DEMO EN SEGUNDOS (cambia este valor cuando quieras)
DEMO_DURATION_SECONDS = 120  # 2 minutos = 120 | 3 minutos = 180 | 1 minuto = 60

PRODUCTOS = {
    "prod_bundle_vj": {
        "nombre": "NX BUNDLE",
        "archivo": "bundle",
        "precio": 15.00,
        "tipo": "bundle",
        "descripcion": "Tres visualizadores en tiempo real. Audio-reactivos. 60 FPS."
    },
    "sub_pro_mensual": {
        "nombre": "NX PRO",
        "archivo": "subscription",
        "precio": 7.00,
        "tipo": "suscripcion",
        "descripcion": "Acceso a todo el catálogo. Contenido nuevo cada mes."
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
            <title>NX ENGINES • Manual</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&family=Tektur:wght@400;500;600;700;800;900&display=swap');
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Inter', sans-serif;
                    background: #ffffff;
                    color: #1a1a1a;
                    line-height: 1.4;
                }
                .container { max-width: 720px; margin: 0 auto; padding: 60px 24px; }
                h1 { font-family: 'Tektur', monospace; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 12px; }
                h2 { font-family: 'Tektur', monospace; font-size: 1rem; font-weight: 600; margin: 24px 0 12px; letter-spacing: -0.01em; text-transform: uppercase; }
                p { color: #555; margin-bottom: 12px; line-height: 1.4; }
                .divider { width: 40px; height: 1px; background: #e0e0e0; margin: 24px 0; }
                .card { border: 1px solid #eaeaea; border-radius: 12px; padding: 20px; margin: 20px 0; background: #fafafa; }
                .key { font-family: monospace; background: #f0f0f0; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; }
                table { width: 100%; border-collapse: collapse; margin: 12px 0; }
                td, th { padding: 8px 0; border-bottom: 1px solid #eee; text-align: left; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 0.75rem; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NX ENGINES</h1>
                <p>Manual de usuario — Visuales en tiempo real</p>
                <div class="divider"></div>
                
                <div class="card">
                    <p><strong>Gracias por adquirir NX ENGINES.</strong> Este manual te ayudará a aprovechar al máximo cada visualizador.</p>
                </div>
                
                <h2>Contenido del bundle</h2>
                <p><strong>NX KALEIDO ENGINE</strong> — Efectos kaleidoscopio, grid VHS y glow.</p>
                <p><strong>NX ASCII ENGINE</strong> — ASCII art, mezcla con webcam y fuego 3D.</p>
                <p><strong>NX GLITCH ENGINE</strong> — Figuras 3D, shaders, glitch, delay y echo.</p>
                
                <h2>Inicio rápido</h2>
                <p>Abre cualquier archivo .html en tu navegador (Chrome, Firefox, Edge). Permite el acceso al micrófono. Conecta tu música y los visuales reaccionarán en tiempo real.</p>
                
                <h2>Controles generales</h2>
                <table>
                    <tr><td><span class="key">TAB</span></td><td>Ocultar o mostrar interfaz</td>
                    <tr><td><span class="key">P</span></td><td>Activar o desactivar micrófono</td>
                    <tr><td><span class="key">O</span></td><td>Cambiar banda de audio (bajo, medios, agudos)</td>
                    <tr><td><span class="key">+ / -</span></td><td>Ajustar intensidad de efectos</td>
                    <tr><td><span class="key">T</span></td><td>Capturar pantalla (PNG)</td>
                    <tr><td><span class="key">Y</span></td><td>Grabar video (WEBM)</td>
                </table>
                
                <h2>Soporte</h2>
                <p>¿Dudas? Escríbenos a <strong>soporte@najarrox.xyz</strong></p>
                
                <div class="footer">
                    <p>NAJARRO X STUDIO · Panamá · 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        zf.writestr("00_MANUAL_NX_ENGINES.html", manual_html)
        
        readme = """========================================
   NAJARRO X STUDIO · NX ENGINES
========================================

Gracias por tu compra.

Este bundle incluye tres visualizadores en tiempo real.

Abre "00_MANUAL_NX_ENGINES.html" para instrucciones.

Soporte: soporte@najarrox.xyz
Web: www.najarrox.xyz

© NAJARRO X STUDIO
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
            <head><meta charset="UTF-8"></head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif; background: #ffffff; padding: 32px;">
                <div style="max-width: 520px; margin: 0 auto; border: 1px solid #eaeaea; border-radius: 20px; padding: 32px;">
                    <h1 style="font-family: 'Tektur', monospace; font-size: 1.5rem; font-weight: 700; margin-bottom: 12px;">Gracias, {nombre}</h1>
                    <p style="color: #555; margin-bottom: 12px;">Tu bundle <strong>{producto['nombre']}</strong> está listo para descargar.</p>
                    <div style="background: #fafafa; padding: 20px; border-radius: 12px; margin: 20px 0;">
                        <p style="margin-bottom: 8px;"><strong>Enlace de descarga</strong></p>
                        <a href="{link_descarga}" style="color: #000; word-break: break-all;">{link_descarga}</a>
                        <p style="margin-top: 12px;"><strong>Contraseña</strong><br><span style="font-family: monospace;">{contrasena}</span></p>
                    </div>
                    <p style="font-size: 0.7rem; color: #999;">Este enlace expira en 7 días.</p>
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
            <head><meta charset="UTF-8"></head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif; background: #ffffff; padding: 32px;">
                <div style="max-width: 520px; margin: 0 auto; border: 1px solid #eaeaea; border-radius: 20px; padding: 32px;">
                    <h1 style="font-family: 'Tektur', monospace; font-size: 1.5rem; font-weight: 700; margin-bottom: 12px;">Bienvenido a NX PRO</h1>
                    <p style="color: #555; margin-bottom: 12px;">Tu suscripción está activa, {nombre}.</p>
                    <div style="background: #fafafa; padding: 20px; border-radius: 12px; margin: 20px 0;">
                        <p style="margin-bottom: 8px;"><strong>Tu vault personal</strong></p>
                        <a href="{link_vault}" style="color: #000;">{link_vault}</a>
                    </div>
                    <p style="font-size: 0.7rem; color: #999;">Guarda este enlace. Se renueva automáticamente.</p>
                </div>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, "NX PRO — Tu suscripción está activa", html_email)
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
# VAULT — CON STATS MÁS GRANDES
# ============================================

@app.route('/vault')
def vault_suscriptor():
    token = request.args.get('token')
    if not token:
        return '''
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Acceso</title></head>
        <body style="font-family: 'Inter', sans-serif; background: #fff; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center; padding: 32px;">
                <h1 style="font-family: 'Tektur', monospace; font-weight: 700; font-size: 1.5rem; margin-bottom: 12px;">Acceso restringido</h1>
                <p style="color: #666; margin-bottom: 12px;">Este contenido es exclusivo para suscriptores.</p>
                <a href="https://www.najarrox.xyz" style="color: #000; border: 1px solid #e0e0e0; padding: 10px 24px; text-decoration: none; display: inline-block; margin-top: 20px;">Suscribirse</a>
            </div>
        </body>
        </html>
        ''', 403
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return "Suscripción expirada", 403
    
    seasons = obtener_temporadas()
    fecha_expiracion = datetime.fromtimestamp(suscripcion["expira"]).strftime('%d/%m/%Y')
    
    html = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NX PRO VAULT</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600&family=Tektur:wght@400;500;600;700;800;900&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background: #ffffff;
                color: #1a1a1a;
                line-height: 1.4;
            }}
            
            .header {{
                border-bottom: 1px solid #eaeaea;
                padding: 24px 32px;
                background: #ffffff;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            .header-inner {{
                max-width: 1280px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                flex-wrap: wrap;
                gap: 20px;
            }}
            
            .logo-area h1 {{
                font-family: 'Tektur', monospace;
                font-size: 1rem;
                font-weight: 700;
                letter-spacing: -0.01em;
                color: #1a1a1a;
            }}
            
            .logo-area p {{
                font-size: 0.65rem;
                color: #999;
                margin-top: 4px;
                letter-spacing: 0.3px;
            }}
            
            .user-area {{
                text-align: right;
            }}
            
            .user-name {{
                font-weight: 500;
                font-size: 0.85rem;
            }}
            
            .user-expiry {{
                font-size: 0.65rem;
                color: #00a86b;
                margin-top: 2px;
            }}
            
            .badge {{
                display: inline-block;
                background: #f0f0f0;
                padding: 2px 10px;
                border-radius: 20px;
                font-size: 0.6rem;
                font-weight: 400;
                margin-top: 6px;
                color: #555;
            }}
            
            .container {{
                max-width: 1280px;
                margin: 0 auto;
                padding: 40px 32px;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1px;
                background: #eaeaea;
                border-radius: 16px;
                overflow: hidden;
                margin-bottom: 60px;
            }}
            
            .stat-card {{
                background: #fff;
                padding: 28px 24px;
                text-align: center;
            }}
            
            .stat-number {{
                font-family: 'Tektur', monospace;
                font-size: 2.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: #1a1a1a;
            }}
            
            .stat-label {{
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #999;
                margin-top: 8px;
            }}
            
            .season {{
                margin-bottom: 60px;
            }}
            
            .season-title {{
                font-family: 'Tektur', monospace;
                font-size: 1rem;
                font-weight: 700;
                letter-spacing: -0.01em;
                margin-bottom: 28px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eaeaea;
            }}
            
            .visual-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 28px;
            }}
            
            .visual-card {{
                border: 1px solid #eaeaea;
                border-radius: 20px;
                background: #ffffff;
                transition: all 0.2s ease;
                cursor: pointer;
                overflow: hidden;
            }}
            
            .visual-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.04);
                border-color: #d0d0d0;
            }}
            
            .visual-preview {{
                height: 180px;
                background: #fafafa;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Tektur', monospace;
                font-size: 2rem;
                font-weight: 700;
                color: #ccc;
                border-bottom: 1px solid #eaeaea;
            }}
            
            .visual-info {{
                padding: 20px;
            }}
            
            .visual-info h3 {{
                font-family: 'Tektur', monospace;
                font-size: 0.9rem;
                font-weight: 700;
                margin-bottom: 6px;
                letter-spacing: -0.01em;
            }}
            
            .visual-info p {{
                font-size: 0.7rem;
                color: #888;
                margin-bottom: 16px;
            }}
            
            .btn-open {{
                background: none;
                border: 1px solid #1a1a1a;
                padding: 6px 18px;
                border-radius: 40px;
                font-size: 0.65rem;
                font-weight: 500;
                cursor: pointer;
                font-family: 'Inter', sans-serif;
                transition: all 0.15s ease;
                color: #1a1a1a;
            }}
            
            .btn-open:hover {{
                background: #1a1a1a;
                color: #fff;
            }}
            
            .footer {{
                border-top: 1px solid #eaeaea;
                padding: 32px 32px;
                text-align: center;
                font-size: 0.65rem;
                color: #999;
            }}
            
            .footer a {{
                color: #1a1a1a;
                text-decoration: none;
            }}
            
            @media (max-width: 768px) {{
                .header-inner {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                .user-area {{
                    text-align: left;
                }}
                .stats-grid {{
                    grid-template-columns: 1fr;
                    gap: 1px;
                }}
                .container {{
                    padding: 28px 20px;
                }}
                .season-title {{
                    font-size: 0.9rem;
                }}
                .visual-grid {{
                    grid-template-columns: 1fr;
                }}
                .stat-number {{
                    font-size: 1.8rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-inner">
                <div class="logo-area">
                    <h1>NAJARRO X · VJ LIVE</h1>
                    <p>Real‑time visual engines</p>
                </div>
                <div class="user-area">
                    <div class="user-name">{suscripcion["nombre"]}</div>
                    <div class="user-expiry">Activo hasta {fecha_expiracion}</div>
                    <div class="badge">Suscripción activa</div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{sum(len(s["visuales"]) for s in seasons)}</div>
                    <div class="stat-label">visuales disponibles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(seasons)}</div>
                    <div class="stat-label">temporadas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">+3</div>
                    <div class="stat-label">nuevos / mes</div>
                </div>
            </div>
    '''
    
    for season in seasons:
        html += f'''
            <div class="season">
                <div class="season-title">{season["nombre"]}</div>
                <div class="visual-grid">
        '''
        for visual in season["visuales"]:
            letter = "K" if "kaleido" in visual["archivo"].lower() else "A" if "ascii" in visual["archivo"].lower() else "G" if "glitch" in visual["archivo"].lower() else "V"
            visual_url = f"{visual['ruta']}?token={token}"
            html += f'''
                    <div class="visual-card" onclick="window.open('{visual_url}', '_blank')">
                        <div class="visual-preview">{letter}</div>
                        <div class="visual-info">
                            <h3>{visual["nombre"]}</h3>
                            <p>Audio‑reactivo · 60 fps</p>
                            <button class="btn-open">Abrir</button>
                        </div>
                    </div>
            '''
        html += '''
                </div>
            </div>
        '''
    
    html += '''
            <div class="footer">
                <p><a href="https://www.najarrox.xyz">najarrox.xyz</a> — soporte@najarrox.xyz</p>
                <p style="margin-top: 8px;">© Najarro X Studio</p>
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
        demo_script = f'''
        <div id="nx-demo-badge" style="position:fixed;bottom:24px;right:24px;background:#ffffff;color:#1a1a1a;font-family:'Inter',-apple-system,sans-serif;padding:8px 16px;z-index:9999;font-size:12px;font-weight:500;border:1px solid #e0e0e0;border-radius:40px;backdrop-filter:blur(8px);box-shadow:0 2px 8px rgba(0,0,0,0.02);pointer-events:none;">
            Demo · {DEMO_DURATION_SECONDS//60}:{(DEMO_DURATION_SECONDS%60):02d}
        </div>
        <script>
            (function() {{
                let tiempo = {DEMO_DURATION_SECONDS};
                let bloqueado = false;
                const badge = document.getElementById('nx-demo-badge');
                if(!badge) return;
                
                function bloquearPantalla() {{
                    if(bloqueado) return;
                    bloqueado = true;
                    
                    if(typeof cancelAnimationFrame !== 'undefined') {{
                        if(window.__NX_ANIMATION_ID__) cancelAnimationFrame(window.__NX_ANIMATION_ID__);
                    }}
                    
                    const blocker = document.createElement('div');
                    blocker.id = 'nx-blocker';
                    blocker.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#ffffff;z-index:100000;display:flex;align-items:center;justify-content:center;font-family:\\'Inter\\',-apple-system,sans-serif;text-align:center;';
                    blocker.innerHTML = `
                        <div style="max-width:400px;padding:32px;">
                            <div style="width:40px;height:1px;background:#e0e0e0;margin:0 auto 24px;"></div>
                            <h1 style="font-family:\\'Tektur\\',monospace;font-weight:700;font-size:1.5rem;margin-bottom:12px;">Demo finalizada</h1>
                            <p style="color:#666;margin-bottom:28px;">El tiempo de prueba ha terminado.</p>
                            <a href="https://nxvjweb.onrender.com/" style="background:#1a1a1a;color:#fff;padding:10px 24px;text-decoration:none;border-radius:40px;display:inline-block;">Adquirir bundle</a>
                            <div style="width:40px;height:1px;background:#e0e0e0;margin:24px auto 0;"></div>
                        </div>
                    `;
                    document.body.appendChild(blocker);
                }}
                
                const interval = setInterval(function() {{
                    if(bloqueado) return;
                    tiempo--;
                    var mins = Math.floor(tiempo/60);
                    var segs = (tiempo%60).toString().padStart(2,'0');
                    if(badge) badge.innerHTML = 'Demo · ' + mins + ':' + segs;
                    
                    if(tiempo <= 10 && tiempo > 0) {{
                        badge.style.borderColor = '#ccc';
                    }}
                    
                    if(tiempo <= 0) {{
                        clearInterval(interval);
                        bloquearPantalla();
                    }}
                }}, 1000);
            }})();
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
    
    demo_script = f'''
    <div id="nx-demo-badge" style="position:fixed;bottom:24px;right:24px;background:#ffffff;color:#1a1a1a;font-family:'Inter',-apple-system,sans-serif;padding:8px 16px;z-index:9999;font-size:12px;font-weight:500;border:1px solid #e0e0e0;border-radius:40px;backdrop-filter:blur(8px);box-shadow:0 2px 8px rgba(0,0,0,0.02);pointer-events:none;">
        Demo · {DEMO_DURATION_SECONDS//60}:{(DEMO_DURATION_SECONDS%60):02d}
    </div>
    <script>
        (function() {{
            let tiempo = {DEMO_DURATION_SECONDS};
            let bloqueado = false;
            const badge = document.getElementById('nx-demo-badge');
            if(!badge) return;
            
            function bloquearPantalla() {{
                if(bloqueado) return;
                bloqueado = true;
                
                if(typeof cancelAnimationFrame !== 'undefined') {{
                    if(window.__NX_ANIMATION_ID__) cancelAnimationFrame(window.__NX_ANIMATION_ID__);
                }}
                
                const blocker = document.createElement('div');
                blocker.id = 'nx-blocker';
                blocker.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#ffffff;z-index:100000;display:flex;align-items:center;justify-content:center;font-family:\\'Inter\\',-apple-system,sans-serif;text-align:center;';
                blocker.innerHTML = `
                    <div style="max-width:400px;padding:32px;">
                        <div style="width:40px;height:1px;background:#e0e0e0;margin:0 auto 24px;"></div>
                        <h1 style="font-family:\\'Tektur\\',monospace;font-weight:700;font-size:1.5rem;margin-bottom:12px;">Demo finalizada</h1>
                        <p style="color:#666;margin-bottom:28px;">El tiempo de prueba ha terminado.</p>
                        <a href="https://nxvjweb.onrender.com/" style="background:#1a1a1a;color:#fff;padding:10px 24px;text-decoration:none;border-radius:40px;display:inline-block;">Adquirir bundle</a>
                        <div style="width:40px;height:1px;background:#e0e0e0;margin:24px auto 0;"></div>
                    </div>
                `;
                document.body.appendChild(blocker);
            }}
            
            const interval = setInterval(function() {{
                if(bloqueado) return;
                tiempo--;
                var mins = Math.floor(tiempo/60);
                var segs = (tiempo%60).toString().padStart(2,'0');
                if(badge) badge.innerHTML = 'Demo · ' + mins + ':' + segs;
                
                if(tiempo <= 10 && tiempo > 0) {{
                    badge.style.borderColor = '#ccc';
                }}
                
                if(tiempo <= 0) {{
                    clearInterval(interval);
                    bloquearPantalla();
                }}
            }}, 1000);
        }})();
    </script>
    '''
    contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/files/images/<path:filename>')
def servir_imagen(filename):
    ruta = os.path.join("files", "images", filename)
    if not os.path.exists(ruta):
        return "", 404
    return send_file(ruta)

# ============================================
# PÁGINA PRINCIPAL — PRECIOS Y FEATURES GIGANTES
# ============================================

@app.route('/')
def home():
    seasons = obtener_temporadas()
    total_visuales = sum(len(s["visuales"]) for s in seasons)
    
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Najarro X — VJ Live Engines</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600&family=Tektur:wght@400;500;600;700;800;900&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background: #ffffff;
                color: #1a1a1a;
                line-height: 1.4;
            }}
            
            .nav {{
                padding: 24px 32px;
                border-bottom: 1px solid #eaeaea;
                max-width: 1280px;
                margin: 0 auto;
                width: 100%;
            }}
            
            .nav-inner {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                flex-wrap: wrap;
                gap: 20px;
            }}
            
            .nav-brand {{
                font-family: 'Tektur', monospace;
                font-size: 0.85rem;
                font-weight: 700;
                letter-spacing: -0.01em;
            }}
            
            .nav-brand span {{
                color: #999;
                font-weight: 400;
            }}
            
            .nav-links a {{
                color: #1a1a1a;
                text-decoration: none;
                font-size: 0.75rem;
                margin-left: 28px;
                transition: opacity 0.2s;
            }}
            
            .nav-links a:hover {{
                opacity: 0.6;
            }}
            
            .hero {{
                max-width: 800px;
                margin: 60px auto 80px;
                padding: 0 32px;
                text-align: center;
            }}
            
            .hero h1 {{
                font-family: 'Tektur', monospace;
                font-size: 4rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                line-height: 1.1;
                margin-bottom: 12px;
            }}
            
            .hero p {{
                font-size: 0.95rem;
                color: #666;
                max-width: 560px;
                margin: 0 auto;
                line-height: 1.4;
            }}
            
            .divider {{
                width: 40px;
                height: 1px;
                background: #e0e0e0;
                margin: 20px auto 0;
            }}
            
            .products {{
                max-width: 1000px;
                margin: 0 auto;
                padding: 0 32px 60px;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 32px;
            }}
            
            .product-card {{
                border: 1px solid #eaeaea;
                border-radius: 24px;
                padding: 32px;
                transition: all 0.2s ease;
                background: #ffffff;
            }}
            
            .product-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.04);
                border-color: #d0d0d0;
            }}
            
            .product-card h2 {{
                font-family: 'Tektur', monospace;
                font-size: 1.2rem;
                font-weight: 700;
                letter-spacing: -0.01em;
                margin-bottom: 8px;
            }}
            
            .product-price {{
                font-family: 'Tektur', monospace;
                font-size: 3.5rem;
                font-weight: 800;
                margin: 20px 0 8px;
                letter-spacing: -0.02em;
                line-height: 1;
            }}
            
            .product-price small {{
                font-size: 1.1rem;
                font-weight: 500;
                color: #888;
            }}
            
            .product-desc {{
                font-size: 0.75rem;
                color: #888;
                margin-bottom: 24px;
                line-height: 1.4;
            }}
            
            .product-link {{
                display: inline-block;
                background: #1a1a1a;
                color: #fff;
                padding: 8px 24px;
                border-radius: 40px;
                text-decoration: none;
                font-size: 0.7rem;
                font-weight: 500;
                transition: background 0.2s;
                margin-right: 12px;
            }}
            
            .product-link-secondary {{
                background: transparent;
                color: #1a1a1a;
                border: 1px solid #e0e0e0;
            }}
            
            .product-link-secondary:hover {{
                background: #f5f5f5;
            }}
            
            .product-link:hover {{
                background: #333;
            }}
            
            .features {{
                max-width: 800px;
                margin: 0 auto;
                padding: 50px 32px;
                border-top: 1px solid #eaeaea;
                display: flex;
                justify-content: center;
                gap: 48px;
                flex-wrap: wrap;
            }}
            
            .feature-item {{
                text-align: center;
            }}
            
            .feature-number {{
                font-family: 'Tektur', monospace;
                font-size: 3rem;
                font-weight: 800;
                margin-bottom: 8px;
                letter-spacing: -0.02em;
                line-height: 1;
            }}
            
            .feature-label {{
                font-size: 0.9rem;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
            
            .footer {{
                border-top: 1px solid #eaeaea;
                padding: 32px 32px;
                text-align: center;
                font-size: 0.65rem;
                color: #999;
            }}
            
            .footer a {{
                color: #1a1a1a;
                text-decoration: none;
            }}
            
            @media (max-width: 768px) {{
                .hero h1 {{
                    font-size: 2.5rem;
                }}
                .products {{
                    grid-template-columns: 1fr;
                    gap: 20px;
                }}
                .nav-links a {{
                    margin-left: 0;
                    margin-right: 20px;
                }}
                .product-card {{
                    padding: 24px;
                }}
                .hero {{
                    margin: 40px auto 50px;
                }}
                .features {{
                    gap: 32px;
                    padding: 40px 20px;
                }}
                .product-price {{
                    font-size: 2.2rem;
                }}
                .product-price small {{
                    font-size: 0.9rem;
                }}
                .feature-number {{
                    font-size: 2rem;
                }}
                .feature-label {{
                    font-size: 0.75rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="nav">
            <div class="nav-inner">
                <div class="nav-brand">NAJARRO X <span>VJ LIVE</span></div>
                <div class="nav-links">
                    <a href="https://www.najarrox.xyz">estudio</a>
                    <a href="/demo/kaleido">demo</a>
                    <a href="mailto:soporte@najarrox.xyz">soporte</a>
                </div>
            </div>
        </div>
        
        <div class="hero">
            <h1>Visuales en tiempo real.<br>Audio‑reactivos.</h1>
            <p>Tres motores generativos que sincronizan imagen y sonido. Ejecuta desde cualquier navegador, sin instalación.</p>
            <div class="divider"></div>
        </div>
        
        <div class="products">
            <div class="product-card">
                <h2>NX Bundle</h2>
                <div class="product-price">15 <small>USD</small></div>
                <div class="product-desc">Incluye los tres visualizadores: Kaleido, ASCII y Glitch. Formato HTML listo para usar.</div>
                <a href="/demo/kaleido" class="product-link product-link-secondary">Probar demo</a>
                <a href="#" class="product-link" onclick="alert('Próximamente en Recurrente')">Comprar</a>
            </div>
            
            <div class="product-card">
                <h2>NX Pro</h2>
                <div class="product-price">7 <small>USD/mes</small></div>
                <div class="product-desc">Acceso a todo el catálogo. Contenido nuevo cada mes. Cancela cuando quieras.</div>
                <a href="https://recurrente.com/p/sub_pro_mensual" class="product-link">Suscribirse</a>
            </div>
        </div>
        
        <div class="features">
            <div class="feature-item">
                <div class="feature-number">{total_visuales}</div>
                <div class="feature-label">visuales</div>
            </div>
            <div class="feature-item">
                <div class="feature-number">60</div>
                <div class="feature-label">fps</div>
            </div>
            <div class="feature-item">
                <div class="feature-number">+3</div>
                <div class="feature-label">nuevos/mes</div>
            </div>
        </div>
        
        <div class="footer">
            <p><a href="https://www.najarrox.xyz">najarrox.xyz</a> — <a href="mailto:soporte@najarrox.xyz">soporte@najarrox.xyz</a></p>
            <p style="margin-top: 8px;">© Najarro X Studio · Panamá</p>
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
        "demo_duration_seconds": DEMO_DURATION_SECONDS,
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
    logger.info(f"🌐 Servidor iniciado en puerto {port}")
    logger.info(f"💰 Bundle: $15 | Suscripción: $7/mes")
    logger.info(f"⏱️ Demo duration: {DEMO_DURATION_SECONDS} segundos")
    app.run(host='0.0.0.0', port=port, debug=False)