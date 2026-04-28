#!/usr/bin/env python3
# server.py - NX PRO VAULT (Versión simplificada - No modifica visualizadores)

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
# CONFIGURACIÓN DE PRODUCTOS
# ============================================

PRODUCTOS = {
    "prod_kaleido_v1": {
        "nombre": "KALEIDO + GRID • GLOW VHS",
        "archivo": "season_01/kaleido.html",
        "precio": 9.99,
        "tipo": "unico"
    },
    "prod_ascii_v1": {
        "nombre": "ASCII MATRIX • WEBCAM • ORGANIC FLAME",
        "archivo": "season_01/ascii.html",
        "precio": 12.99,
        "tipo": "unico"
    },
    "prod_glitch_v1": {
        "nombre": "VJ GLITCH ENGINE • AUDIO REACTIVE",
        "archivo": "season_01/glitch.html",
        "precio": 14.99,
        "tipo": "unico"
    },
    "prod_bundle_vj": {
        "nombre": "BUNDLE: Los 3 Visualizadores",
        "archivo": "bundle",
        "precio": 29.99,
        "tipo": "bundle"
    },
    "sub_pro_mensual": {
        "nombre": "SUSCRIPCIÓN NX PRO",
        "archivo": "subscription",
        "precio": 7.00,
        "tipo": "suscripcion"
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
    """Obtiene las temporadas disponibles"""
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
    """Crea un ZIP con los 3 visualizadores"""
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
        
        readme = """========================================
   NAJARRO X STUDIO - NX ENGINES
========================================

🎬 ¡Gracias por tu compra!

Este bundle incluye 3 visualizadores en tiempo real.

Visita najarrox.xyz para más información.

© 2026 NAJARRO X STUDIO
"""
        zf.writestr("README_NX_ENGINES.txt", readme)
    memory_file.seek(0)
    return memory_file

def enviar_email_simple(destinatario, nombre, asunto, cuerpo_html):
    """Envía email usando SMTP de Gmail"""
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
# WEBHOOK DE RECURRENTE
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error"}), 400
        
        event_type = data.get('event_type')
        logger.info(f"📨 Evento: {event_type}")
        
        # Pago único exitoso
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
            <body style="font-family: monospace; background: #0a0a0a; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1a1a1a; border: 2px solid #8b5cf6; padding: 30px;">
                    <h1 style="color: #8b5cf6;">🎬 ¡Gracias por tu compra, {nombre}!</h1>
                    <p><strong>{producto['nombre']}</strong></p>
                    <div style="background: #0a0a0a; color: white; padding: 20px; margin: 20px 0;">
                        <p>🔗 <strong>TU ENLACE DE DESCARGA:</strong></p>
                        <a href="{link_descarga}" style="color: #8b5cf6;">{link_descarga}</a>
                        <p style="margin-top: 15px;">🔐 <strong>CONTRASEÑA:</strong> {contrasena}</p>
                    </div>
                    <p>Este enlace expira en 7 días.</p>
                    <p>NAJARRO X STUDIO</p>
                </div>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, f"Tu {producto['nombre']} está listo", html_email)
            logger.info(f"✅ Venta completada: {producto_id} -> {email}")
            return jsonify({"status": "ok"}), 200
        
        # Suscripción activada
        elif event_type == 'subscription.active':
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            
            if not email:
                return jsonify({"status": "error"}), 400
            
            token_sub = secrets.token_urlsafe(32)
            fecha_expiracion = datetime.now().timestamp() + 30 * 24 * 3600  # 30 días
            
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
            <body style="font-family: monospace; background: #0a0a0a; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1a1a1a; border: 2px solid #8b5cf6; padding: 30px;">
                    <h1 style="color: #8b5cf6;">🎬 ¡Bienvenido a NX PRO, {nombre}!</h1>
                    <p>Tu suscripción está activa.</p>
                    <div style="background: #0a0a0a; color: white; padding: 20px; margin: 20px 0;">
                        <p>🔗 <strong>TU VAULT PERSONAL:</strong></p>
                        <a href="{link_vault}" style="color: #8b5cf6;">{link_vault}</a>
                    </div>
                    <p>Guarda este enlace. Se renueva automáticamente cada mes.</p>
                </div>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, "NX PRO - Tu suscripción está activa", html_email)
            logger.info(f"✅ Suscripción activada para {email}")
            return jsonify({"status": "ok", "token": token_sub}), 200
        
        # Suscripción cancelada
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
# ENDPOINTS DE DESCARGA
# ============================================

@app.route('/descargar/<token>')
def descargar_archivo(token):
    """Descarga de productos comprados (pago único)"""
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
        return "Enlace expirado (máximo 7 días)", 403
    
    producto_id = datos["producto_id"]
    producto = PRODUCTOS.get(producto_id)
    
    if not producto:
        return "Producto no encontrado", 404
    
    # Bundle
    if producto_id == "prod_bundle_vj":
        return send_file(
            crear_zip_bundle(), 
            as_attachment=True, 
            download_name=f"NX_BUNDLE_{datetime.now().strftime('%Y%m%d')}.zip", 
            mimetype="application/zip"
        )
    
    # Producto individual
    ruta_archivo = os.path.join("files", producto["archivo"])
    if not os.path.exists(ruta_archivo):
        logger.error(f"Archivo no encontrado: {ruta_archivo}")
        return "Archivo no encontrado", 404
    
    return send_file(
        ruta_archivo, 
        as_attachment=True, 
        download_name=f"NX_{producto_id}.html", 
        mimetype="text/html"
    )

@app.route('/verificar-suscripcion')
def verificar_suscripcion_endpoint():
    """Verifica si un token de suscripción es válido"""
    token = request.args.get('token')
    if not token:
        return jsonify({"activa": False, "error": "Token requerido"}), 400
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return jsonify({"activa": False, "error": "Token inválido o expirado"}), 200
    
    return jsonify({
        "activa": True,
        "expira": suscripcion["expira"],
        "email": suscripcion["email"],
        "nombre": suscripcion["nombre"]
    })

# ============================================
# VAULT PARA SUSCRIPTORES
# ============================================

@app.route('/vault')
def vault_suscriptor():
    """Menú principal para suscriptores PRO"""
    token = request.args.get('token')
    if not token:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Acceso Pro Requerido</title></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>🔐 ACCESO PRO REQUERIDO</h2>
                <p>Este contenido es exclusivo para suscriptores.</p>
                <a href="https://www.najarrox.xyz" style="color:#8b5cf6;">Suscríbete en najarrox.xyz</a>
            </div>
        </body>
        </html>
        ''', 403
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Suscripción Inválida</title></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>⚠️ SUSCRIPCIÓN EXPIRADA</h2>
                <p>Tu suscripción no está activa o ha expirado.</p>
                <a href="https://www.najarrox.xyz" style="color:#8b5cf6;">Renovar ahora</a>
            </div>
        </body>
        </html>
        ''', 403
    
    seasons = obtener_temporadas()
    fecha_expiracion = datetime.fromtimestamp(suscripcion["expira"]).strftime('%d/%m/%Y')
    
    html = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NX PRO VAULT • {suscripcion["nombre"]}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 40px; border-radius: 20px; margin-bottom: 30px; border-left: 8px solid #8b5cf6; }}
            .header h1 {{ font-size: 2rem; color: #8b5cf6; }}
            .badge {{ display: inline-block; background: #00c853; color: black; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            .season {{ margin-bottom: 40px; }}
            .season-title {{ font-size: 1.5rem; color: #ffaa44; border-bottom: 2px solid #ffaa44; padding-bottom: 10px; margin-bottom: 20px; display: inline-block; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; margin-top: 20px; }}
            .card {{ background: #1a1a1a; border-radius: 15px; overflow: hidden; cursor: pointer; border: 1px solid #333; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(139,92,246,0.3); border-color: #8b5cf6; }}
            .card-preview {{ height: 160px; background: linear-gradient(135deg, #2a2a3e, #1a1a2e); display: flex; align-items: center; justify-content: center; font-size: 48px; }}
            .card-info {{ padding: 20px; }}
            .card-info h3 {{ color: #8b5cf6; margin-bottom: 8px; }}
            .btn-open {{ display: inline-block; background: #8b5cf6; color: black; padding: 8px 16px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 12px; }}
            .status {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 30px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; }}
            .footer {{ text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #333; font-size: 12px; color: #666; }}
            @media (max-width: 768px) {{ .header h1 {{ font-size: 1.3rem; }} .season-title {{ font-size: 1.2rem; }} .grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 NX PRO VAULT</h1>
                <p>Bienvenido, <strong>{suscripcion["nombre"]}</strong> ({suscripcion["email"]})</p>
                <div class="badge">✅ SUSCRIPCIÓN ACTIVA</div>
                <p style="margin-top: 15px; font-size: 12px;">Expira: <strong>{fecha_expiracion}</strong></p>
            </div>
            
            <div class="status">
                <div>📦 Biblioteca: <strong>{sum(len(s["visuales"]) for s in seasons)} visuales</strong></div>
                <div>🎨 Temporadas: <strong>{len(seasons)}</strong></div>
                <div>🔄 Nuevos visuales: <strong>Cada mes</strong></div>
            </div>
    '''
    
    for season in seasons:
        html += f'''
            <div class="season">
                <div class="season-title">📀 {season["nombre"]}</div>
                <div class="grid">
        '''
        for visual in season["visuales"]:
            emoji = "🌀" if "kaleido" in visual["archivo"].lower() else "🔥" if "ascii" in visual["archivo"].lower() else "🎛️" if "glitch" in visual["archivo"].lower() else "✨"
            visual_url = f"{visual['ruta']}?token={token}"
            html += f'''
                    <div class="card" onclick="window.open('{visual_url}', '_blank')">
                        <div class="card-preview">{emoji}</div>
                        <div class="card-info">
                            <h3>{visual["nombre"]}</h3>
                            <p>Visual en tiempo real • Audio-reactivo</p>
                            <button class="btn-open">🎬 ABRIR</button>
                        </div>
                    </div>
            '''
        html += '''
                </div>
            </div>
        '''
    
    html += '''
            <div class="footer">
                <p>🔒 Visuales exclusivos para suscriptores NX PRO</p>
                <p>© 2026 NAJARRO X STUDIO · soporte@najarrox.xyz</p>
                <p><a href="https://www.najarrox.xyz" style="color:#8b5cf6;">najarrox.xyz</a></p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

# ============================================
# SERVIDOR DE VISUALES (con overlay simple)
# ============================================

@app.route('/visual/<season>/<filename>')
def servir_visual(season, filename):
    """Sirve los visualizadores con verificación de suscripción"""
    token = request.args.get('token')
    
    # Verificar token si existe
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
    
    # SOLO para modo DEMO (sin token), agregamos un overlay simple que NO interfiere
    if not modo_suscriptor:
        demo_script = '''
        <div id="nx-demo-badge" style="position:fixed;bottom:20px;right:20px;background:rgba(0,0,0,0.85);color:#ffaa44;font-family:monospace;padding:10px 16px;z-index:9999;font-size:13px;font-weight:bold;border-right:3px solid #ffaa44;border-radius:8px 0 0 8px;backdrop-filter:blur(8px);pointer-events:none;">
            🎬 DEMO | najarrox.xyz
        </div>
        <script>
            (function() {
                let tiempo = 120;
                const badge = document.getElementById('nx-demo-badge');
                if(!badge) return;
                
                const interval = setInterval(function() {
                    tiempo--;
                    var mins = Math.floor(tiempo/60);
                    var segs = (tiempo%60).toString().padStart(2,'0');
                    if(badge) badge.innerHTML = '⏱️ DEMO: ' + mins + ':' + segs + ' | najarrox.xyz';
                    if(tiempo <= 0) {
                        clearInterval(interval);
                        if(badge) badge.innerHTML = '⏰ DEMO EXPIRADA | Compra en najarrox.xyz';
                        badge.style.borderRightColor = '#ff4444';
                        badge.style.color = '#ff8888';
                    }
                }, 1000);
            })();
        </script>
        '''
        # Insertar antes de </body>
        contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

# ============================================
# DEMO PÚBLICA
# ============================================

@app.route('/demo/kaleido')
def demo_kaleido():
    """Demo pública del visualizador Kaleido (con overlay de tiempo limitado)"""
    ruta = os.path.join("files", "season_01", "kaleido.html")
    if not os.path.exists(ruta):
        return "Demo no disponible", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Mismo overlay simple para la demo
    demo_script = '''
    <div id="nx-demo-badge" style="position:fixed;bottom:20px;right:20px;background:rgba(0,0,0,0.85);color:#ffaa44;font-family:monospace;padding:10px 16px;z-index:9999;font-size:13px;font-weight:bold;border-right:3px solid #ffaa44;border-radius:8px 0 0 8px;backdrop-filter:blur(8px);pointer-events:none;">
        🎬 DEMO | najarrox.xyz
    </div>
    <script>
        (function() {
            let tiempo = 120;
            const badge = document.getElementById('nx-demo-badge');
            if(!badge) return;
            
            const interval = setInterval(function() {
                tiempo--;
                var mins = Math.floor(tiempo/60);
                var segs = (tiempo%60).toString().padStart(2,'0');
                if(badge) badge.innerHTML = '⏱️ DEMO: ' + mins + ':' + segs + ' | najarrox.xyz';
                if(tiempo <= 0) {
                    clearInterval(interval);
                    if(badge) badge.innerHTML = '⏰ DEMO EXPIRADA | Compra en najarrox.xyz';
                    badge.style.borderRightColor = '#ff4444';
                    badge.style.color = '#ff8888';
                }
            }, 1000);
        })();
    </script>
    '''
    contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

# ============================================
# PÁGINAS PÚBLICAS
# ============================================

@app.route('/')
def home():
    seasons = obtener_temporadas()
    total_visuales = sum(len(s["visuales"]) for s in seasons)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NAJARRO X STUDIO - VJ Engines</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: white; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .card {{ background: #1a1a1a; border: 2px solid #8b5cf6; padding: 40px; margin-bottom: 20px; text-align: center; }}
            h1 {{ font-size: 2rem; border-left: 8px solid #8b5cf6; padding-left: 20px; margin-bottom: 20px; display: inline-block; }}
            .status {{ color: #00c853; font-weight: bold; }}
            .productos {{ display: flex; flex-wrap: wrap; gap: 20px; margin-top: 30px; }}
            .producto {{ background: #0a0a0a; border: 1px solid #333; padding: 20px; flex: 1; min-width: 200px; }}
            .producto h3 {{ color: #8b5cf6; margin-bottom: 10px; }}
            .precio {{ font-size: 1.5rem; color: #00c853; margin: 10px 0; }}
            .demo {{ color: #ffaa44; text-decoration: none; font-size: 12px; }}
            .btn-comprar {{ display: inline-block; background: #8b5cf6; color: black; padding: 10px 20px; text-decoration: none; font-weight: bold; margin-top: 10px; border-radius: 5px; }}
            footer {{ margin-top: 40px; text-align: center; color: #555; font-size: 11px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🚀 NAJARRO X STUDIO</h1>
                <p class="status">✅ SISTEMA NX PRO VAULT ACTIVO</p>
                <p>{total_visuales} visuales disponibles • +3 nuevos cada mes</p>
            </div>
            
            <div class="productos">
                <div class="producto">
                    <h3>🌀 KALEIDO + GRID</h3>
                    <div class="precio">$9.99 USD</div>
                    <a href="/demo/kaleido" class="demo">🎬 Probar Demo</a>
                </div>
                <div class="producto">
                    <h3>🎛️ NX PRO</h3>
                    <div class="precio">$7/mes</div>
                    <a href="https://recurrente.com/p/sub_pro_mensual" class="btn-comprar">🎯 SUSCRIBIRME</a>
                </div>
            </div>
            
            <div class="card" style="margin-top:20px;">
                <p>🎨 <a href="https://www.najarrox.xyz" style="color:#8b5cf6;">najarrox.xyz</a> | 🔒 Descargas protegidas</p>
                <p>📊 Estado: Online | Visuales disponibles: {total_visuales}</p>
            </div>
            
            <footer>NAJARRO X STUDIO · Panamá 2026</footer>
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
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 NX PRO VAULT iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)