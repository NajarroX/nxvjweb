#!/usr/bin/env python3
# server.py - NX PRO VAULT (Con botón DEMO gigante con glitch)

from flask import Flask, request, jsonify, send_file, abort, redirect
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

DEMO_DURATION_SECONDS = 120

PRODUCTOS = {
    "prod_jfvog09k": {
        "nombre": "NX VJ LIVE PACK",
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
# FUNCIONES AUXILIARES (igual que antes)
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
        
        manual_html = """<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Manual</title><style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Tektur:wght@400;500;600;700&display=swap');body{font-family:'Inter',sans-serif;background:#fff;color:#1a1a1a;line-height:1.4;padding:40px;max-width:800px;margin:0 auto;}h1{font-family:'Tektur',monospace;font-size:2rem;}h2{font-family:'Tektur',monospace;font-size:1rem;text-transform:uppercase;margin-top:32px;}.card{border:1px solid #eaeaea;border-radius:12px;padding:20px;margin:20px 0;background:#fafafa;}.key{background:#f0f0f0;padding:2px 8px;border-radius:6px;font-family:monospace;}</style></head><body><h1>NX ENGINES</h1><p>Manual de usuario</p><div class='card'><p>Gracias por adquirir NX ENGINES.</p></div><h2>Contenido</h2><p><strong>NX KALEIDO ENGINE</strong> — Efectos kaleidoscopio, grid VHS y glow.</p><p><strong>NX ASCII ENGINE</strong> — ASCII art, mezcla con webcam y fuego 3D.</p><p><strong>NX GLITCH ENGINE</strong> — Figuras 3D, shaders, glitch, delay y echo.</p><h2>Controles</h2><table><tr><td><span class='key'>TAB</span></td><td>Ocultar UI</td></tr><tr><td><span class='key'>P</span></td><td>Micrófono</td></tr><tr><td><span class='key'>O</span></td><td>Banda de audio</td></tr><tr><td><span class='key'>T</span></td><td>Capturar PNG</td></tr><tr><td><span class='key'>Y</span></td><td>Grabar video</td></tr></table><div class='footer'><p>NAJARRO X STUDIO · soporte@najarrox.xyz</p></div></body></html>"""
        zf.writestr("00_MANUAL_NX_ENGINES.html", manual_html)
        zf.writestr("README.txt", "NX ENGINES Bundle - Gracias por tu compra!")
    
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
            html_email = f"<h1>Gracias {nombre}</h1><p>Tu {producto['nombre']} está listo.</p><a href='{link_descarga}'>Descargar</a><p>Contraseña: {contrasena}</p>"
            
            enviar_email_simple(email, nombre, f"Tu {producto['nombre']} está listo", html_email)
            return jsonify({"status": "ok"}), 200
        
        elif event_type == 'subscription.create':
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            if not email:
                return jsonify({"status": "error"}), 400
            
            token_sub = secrets.token_urlsafe(32)
            suscripciones_activas[token_sub] = {
                "email": email, "nombre": nombre,
                "expira": datetime.now().timestamp() + 30*24*3600, "activa": True
            }
            link_vault = f"https://{request.host}/vault?token={token_sub}"
            html_email = f"<h1>Bienvenido {nombre}</h1><p>Tu suscripción NX PRO está activa.</p><a href='{link_vault}'>Acceder al Vault</a>"
            enviar_email_simple(email, nombre, "NX PRO Activada", html_email)
            return jsonify({"status": "ok"}), 200
        
        elif event_type == 'subscription.cance.':
            email = data.get('customer', {}).get('email')
            for token, sub in suscripciones_activas.items():
                if sub["email"] == email:
                    suscripciones_activas[token]["activa"] = False
            return jsonify({"status": "ok"}), 200
        
        return jsonify({"status": "ignored"}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"status": "error"}), 500


@app.route('/descargar/<token>')
def descargar_archivo(token):
    for datos in descargas_autorizadas.values():
        if datos.get("token") == token:
            if datetime.now().timestamp() - datos["timestamp"] > 7*24*3600:
                return "Enlace expirado", 403
            return send_file(crear_zip_bundle(), as_attachment=True, download_name="NX_BUNDLE.zip")
    return "Enlace inválido", 404


@app.route('/verificar-suscripcion')
def verificar_suscripcion_endpoint():
    token = request.args.get('token')
    if not token:
        return jsonify({"activa": False}), 400
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return jsonify({"activa": False}), 200
    return jsonify({"activa": True, "expira": suscripcion["expira"], "nombre": suscripcion["nombre"]})


@app.route('/vault')
def vault_suscriptor():
    token = request.args.get('token')
    if not token:
        return "Acceso restringido", 403
    suscripcion = verificar_suscripcion(token)
    if not suscripcion:
        return "Suscripción expirada", 403
    
    seasons = obtener_temporadas()
    html = f"<h1>NX PRO VAULT - {suscripcion['nombre']}</h1><p>Activo hasta {datetime.fromtimestamp(suscripcion['expira']).strftime('%d/%m/%Y')}</p>"
    for season in seasons:
        html += f"<h2>{season['nombre']}</h2>"
        for v in season['visuales']:
            html += f"<a href='{v['ruta']}?token={token}'><button>{v['nombre']}</button></a>"
    return html


@app.route('/visual/<season>/<filename>')
def servir_visual(season, filename):
    token = request.args.get('token')
    modo_suscriptor = token and verificar_suscripcion(token) is not None
    
    ruta = os.path.join("files", season, filename)
    if not os.path.exists(ruta):
        return "No encontrado", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    if not modo_suscriptor:
        demo_script = f'''
        <div style="position:fixed;bottom:20px;right:20px;background:#fff;border:1px solid #eaeaea;border-radius:40px;padding:8px 20px;font-family:monospace;z-index:9999;">Demo · {DEMO_DURATION_SECONDS//60}:{(DEMO_DURATION_SECONDS%60):02d}</div>
        <script>let t={DEMO_DURATION_SECONDS};setInterval(()=>{{t--;if(t<=0){{document.body.innerHTML='<div style=\"text-align:center;padding:50px;\"><h1>Demo finalizada</h1><a href=\"/\">Comprar bundle</a></div>';}}}},1000);</script>
        '''
        contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido


@app.route('/demo/kaleido')
def demo_kaleido():
    ruta = os.path.join("files", "season_01", "kaleido.html")
    if not os.path.exists(ruta):
        return "Demo no disponible", 404
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    demo_script = f'''
    <div style="position:fixed;bottom:20px;right:20px;background:#fff;border:1px solid #eaeaea;border-radius:40px;padding:8px 20px;font-family:monospace;z-index:9999;">Demo · {DEMO_DURATION_SECONDS//60}:{(DEMO_DURATION_SECONDS%60):02d}</div>
    <script>let t={DEMO_DURATION_SECONDS};setInterval(()=>{{t--;if(t<=0){{document.body.innerHTML='<div style=\"text-align:center;padding:50px;\"><h1>Demo finalizada</h1><a href=\"/\">Comprar bundle</a></div>';}}}},1000);</script>
    '''
    contenido = contenido.replace('</body>', demo_script + '</body>')
    return contenido


@app.route('/files/images/<path:filename>')
def servir_imagen(filename):
    ruta = os.path.join("files", "images", filename)
    if not os.path.exists(ruta):
        return "", 404
    return send_file(ruta)


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
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
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
                max-width: 900px;
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
                margin-bottom: 16px;
            }}
            
            .hero p {{
                font-size: 1rem;
                color: #666;
                max-width: 560px;
                margin: 0 auto;
                line-height: 1.4;
            }}
            
            /* ============================================
               BOTÓN DEMO GIGANTE CON GLITCH
            ============================================ */
            
            .demo-container {{
                margin: 48px auto 40px;
                position: relative;
                width: 100%;
                display: flex;
                justify-content: center;
            }}
            
            .demo-button {{
                position: relative;
                display: inline-block;
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                color: #ffffff;
                font-family: 'Tektur', monospace;
                font-size: 1.8rem;
                font-weight: 800;
                letter-spacing: 4px;
                text-transform: uppercase;
                text-decoration: none;
                padding: 24px 56px;
                border-radius: 80px;
                border: none;
                cursor: pointer;
                transition: all 0.1s ease;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                z-index: 1;
                text-align: center;
                min-width: 450px;
                animation: soft-pulse 2s infinite;
            }}
            
            .demo-button .demo-text {{
                position: relative;
                z-index: 3;
                display: inline-block;
            }}
            
            .demo-button .demo-glitch-layer,
            .demo-button .demo-glitch-layer2 {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
                border-radius: 80px;
                opacity: 0;
                pointer-events: none;
            }}
            
            .demo-button .demo-glitch-layer {{
                color: #ff00cc;
                text-shadow: -2px 0 #00ffcc;
                transform: translateX(-4px);
            }}
            
            .demo-button .demo-glitch-layer2 {{
                color: #00ffcc;
                text-shadow: 2px 0 #ff00cc;
                transform: translateX(4px);
            }}
            
            .demo-button:hover {{
                animation: glitch-pulse 0.3s infinite alternate;
                box-shadow: 0 0 40px rgba(255, 0, 204, 0.5);
            }}
            
            .demo-button:hover .demo-glitch-layer {{
                animation: glitch-offset 0.15s infinite alternate;
                opacity: 0.7;
            }}
            
            .demo-button:hover .demo-glitch-layer2 {{
                animation: glitch-offset2 0.12s infinite alternate;
                opacity: 0.7;
            }}
            
            @keyframes glitch-pulse {{
                0% {{ background: linear-gradient(135deg, #1a1a1a, #2a2a2a); transform: scale(1); }}
                25% {{ background: linear-gradient(135deg, #ff00cc, #1a1a1a); transform: scale(1.01); }}
                50% {{ background: linear-gradient(135deg, #1a1a1a, #00ffcc); transform: scale(1); }}
                75% {{ background: linear-gradient(135deg, #ff00cc, #00ffcc); transform: scale(1.01); }}
                100% {{ background: linear-gradient(135deg, #1a1a1a, #2a2a2a); transform: scale(1); }}
            }}
            
            @keyframes glitch-offset {{
                0% {{ transform: translateX(-6px); opacity: 0.6; }}
                100% {{ transform: translateX(6px); opacity: 0.9; }}
            }}
            
            @keyframes glitch-offset2 {{
                0% {{ transform: translateX(6px); opacity: 0.6; }}
                100% {{ transform: translateX(-6px); opacity: 0.9; }}
            }}
            
            @keyframes soft-pulse {{
                0% {{ box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); }}
                50% {{ box-shadow: 0 10px 50px rgba(255, 0, 204, 0.3); }}
                100% {{ box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); }}
            }}
            
            .divider {{
                width: 40px;
                height: 1px;
                background: #e0e0e0;
                margin: 32px auto 0;
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
                .hero h1 {{ font-size: 2.2rem; }}
                .demo-button {{ font-size: 0.9rem; padding: 16px 24px; letter-spacing: 2px; min-width: 280px; }}
                .demo-container {{ margin: 32px auto 24px; }}
                .products {{ grid-template-columns: 1fr; gap: 20px; }}
                .nav-links a {{ margin-left: 0; margin-right: 20px; }}
                .product-card {{ padding: 24px; }}
                .hero {{ margin: 40px auto 50px; }}
                .features {{ gap: 32px; padding: 40px 20px; }}
                .product-price {{ font-size: 2.2rem; }}
                .feature-number {{ font-size: 2rem; }}
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
            
            <div class="demo-container">
                <a href="/demo/kaleido" class="demo-button" id="demoButton">
                    <span class="demo-text">🎬 PROBAR DEMO GRATIS</span>
                    <span class="demo-glitch-layer">🎬 PROBAR DEMO GRATIS</span>
                    <span class="demo-glitch-layer2">🎬 PROBAR DEMO GRATIS</span>
                </a>
            </div>
            
            <div class="divider"></div>
        </div>
        
        <div class="products">
            <div class="product-card">
                <h2>NX Bundle</h2>
                <div class="product-price">15 <small>USD</small></div>
                <div class="product-desc">Incluye los tres visualizadores: Kaleido, ASCII y Glitch. Formato HTML listo para usar.</div>
                <a href="/demo/kaleido" class="product-link product-link-secondary">Probar demo</a>
                <a href="https://app.recurrente.com/s/najarrox-store/vj-live-pack" class="product-link" target="_blank">Comprar</a>
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
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Servidor iniciado en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)