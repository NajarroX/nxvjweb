#!/usr/bin/env python3
# server.py - Servidor NX PRO VAULT con nombres de archivos correctos

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
# CONFIGURACIÓN - NOMBRES CORRECTOS DE ARCHIVOS
# ============================================

PRODUCTOS = {
    "prod_kaleido_v1": {
        "nombre": "KALEIDO + GRID • GLOW VHS",
        "archivo": "season_01/kaleido.html",     # ← nombre correcto
        "precio": 9.99,
        "tipo": "unico"
    },
    "prod_ascii_v1": {
        "nombre": "ASCII MATRIX • WEBCAM • ORGANIC FLAME",
        "archivo": "season_01/ascii.html",       # ← nombre correcto
        "precio": 12.99,
        "tipo": "unico"
    },
    "prod_glitch_v1": {
        "nombre": "VJ GLITCH ENGINE • AUDIO REACTIVE",
        "archivo": "season_01/glitch.html",      # ← nombre correcto
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
            <body style="font-family: monospace;">
                <h1>🎬 ¡Gracias por tu compra, {nombre}!</h1>
                <p><strong>{producto['nombre']}</strong></p>
                <div style="background:#0a0a0a; color:white; padding:20px;">
                    <p>🔗 <strong>TU ENLACE DE DESCARGA:</strong></p>
                    <a href="{link_descarga}" style="color:#8b5cf6;">{link_descarga}</a>
                    <p style="margin-top:15px;">🔐 <strong>CONTRASEÑA:</strong> {contrasena}</p>
                </div>
                <p>Este enlace expira en 7 días.</p>
                <p>NAJARRO X STUDIO</p>
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
            <body style="font-family: monospace;">
                <h1>🎬 ¡Bienvenido a NX PRO, {nombre}!</h1>
                <p>Tu suscripción está activa.</p>
                <div style="background:#0a0a0a; color:white; padding:20px;">
                    <p>🔗 <strong>TU VAULT PERSONAL:</strong></p>
                    <a href="{link_vault}" style="color:#8b5cf6;">{link_vault}</a>
                </div>
                <p>Guarda este enlace. Se renueva automáticamente cada mes.</p>
            </body>
            </html>
            """
            
            enviar_email_simple(email, nombre, "NX PRO - Tu suscripción está activa", html_email)
            return jsonify({"status": "ok", "token": token_sub}), 200
        
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# ENDPOINTS DE DESCARGA
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
        return "Enlace expirado (máximo 7 días)", 403
    
    producto_id = datos["producto_id"]
    producto = PRODUCTOS.get(producto_id)
    
    if not producto:
        return "Producto no encontrado", 404
    
    if producto_id == "prod_bundle_vj":
        return send_file(crear_zip_bundle(), as_attachment=True, download_name=f"NX_BUNDLE_{datetime.now().strftime('%Y%m%d')}.zip", mimetype="application/zip")
    
    ruta_archivo = os.path.join("files", producto["archivo"])
    if not os.path.exists(ruta_archivo):
        logger.error(f"Archivo no encontrado: {ruta_archivo}")
        return "Archivo no encontrado", 404
    
    return send_file(ruta_archivo, as_attachment=True, download_name=f"NX_{producto_id}.html", mimetype="text/html")

@app.route('/verificar-suscripcion')
def verificar_suscripcion_endpoint():
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

@app.route('/vault')
def vault_suscriptor():
    token = request.args.get('token')
    if not token:
        return "Se requiere token de suscripción", 403
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return "Suscripción inválida o expirada", 403
    
    seasons = obtener_temporadas()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NX PRO VAULT - {suscripcion['nombre']}</title>
        <style>
            body {{ background: #0a0a0a; color: white; font-family: monospace; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: #1a1a1a; padding: 30px; border-left: 5px solid #8b5cf6; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 20px; cursor: pointer; }}
            .card:hover {{ border-color: #8b5cf6; transform: translateY(-5px); transition: 0.2s; }}
            .btn {{ background: #8b5cf6; color: black; padding: 10px 20px; text-decoration: none; display: inline-block; margin-top: 15px; }}
            .badge {{ background: #00c853; color: black; padding: 5px 10px; border-radius: 20px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 NX PRO VAULT</h1>
                <p>Bienvenido, <strong>{suscripcion['nombre']}</strong></p>
                <div class="badge">✅ SUSCRIPCIÓN ACTIVA</div>
            </div>
    """
    
    for season in seasons:
        html += f"<h2>📀 {season['nombre']}</h2><div class='grid'>"
        for visual in season["visuales"]:
            visual_url = f"{visual['ruta']}?token={token}"
            html += f"""
                <div class="card" onclick="window.open('{visual_url}', '_blank')">
                    <h3>🎨 {visual['nombre']}</h3>
                    <p>Visual en tiempo real • Audio-reactivo</p>
                    <button class="btn">🎬 ABRIR</button>
                </div>
            """
        html += "</div>"
    
    html += """
            <div style="text-align: center; margin-top: 50px; color: #666;">
                <p>© 2026 NAJARRO X STUDIO</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/visual/<season>/<filename>')
def servir_visual(season, filename):
    token = request.args.get('token')
    if not token:
        return "Se requiere token", 403
    
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return "Suscripción inválida", 403
    
    ruta = os.path.join("files", season, filename)
    if not os.path.exists(ruta):
        return "Visual no encontrado", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/demo/kaleido')
def demo_kaleido():
    ruta = os.path.join("files", "season_01", "kaleido.html")
    if not os.path.exists(ruta):
        return "Demo no disponible", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/')
def home():
    seasons = obtener_temporadas()
    total = sum(len(s["visuales"]) for s in seasons)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NAJARRO X STUDIO</title>
        <style>
            body {{ background: #0a0a0a; color: white; font-family: monospace; text-align: center; padding: 50px; }}
            .card {{ background: #1a1a1a; border: 2px solid #8b5cf6; padding: 40px; max-width: 600px; margin: 0 auto; }}
            .status {{ color: #00c853; }}
            a {{ color: #8b5cf6; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 NAJARRO X STUDIO</h1>
            <p class="status">✅ SISTEMA ACTIVO</p>
            <p>{total} visuales disponibles • +3 nuevos cada mes</p>
            <p><a href="/demo/kaleido">🎬 PROBAR DEMO GRATIS</a></p>
            <p style="margin-top: 20px;"><a href="https://www.najarrox.xyz">najarrox.xyz</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "activo",
        "temporadas": len(obtener_temporadas()),
        "suscriptores": len(suscripciones_activas),
        "descargas": len(descargas_autorizadas),
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
    app.run(host='0.0.0.0', port=port, debug=False)