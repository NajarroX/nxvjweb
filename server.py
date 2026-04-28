#!/usr/bin/env python3
# server.py - Servidor Flask con webhook, múltiples productos y descarga directa desde Render

from flask import Flask, request, jsonify, send_file, abort
import os
import logging
import hashlib
import random
import string
import secrets
from datetime import datetime
from email_sender import enviar_email
import zipfile
from io import BytesIO

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN DE PRODUCTOS
# ============================================

# Mapeo de IDs de Recurrente a productos locales
PRODUCTOS = {
    "prod_kaleido_v1": {
        "nombre": "KALEIDO + GRID • GLOW VHS",
        "archivo": "kaleido_v1.html",
        "precio": 9.99,
        "descripcion": "Visual psicodélico con kaleidoscopio, grid VHS y glow"
    },
    "prod_ascii_v1": {
        "nombre": "ASCII MATRIX • WEBCAM • ORGANIC FLAME",
        "archivo": "ascii_v1.html",
        "precio": 12.99,
        "descripcion": "ASCII art en tiempo real, webcam mix, partículas de fuego"
    },
    "prod_glitch_v1": {
        "nombre": "VJ GLITCH ENGINE • AUDIO REACTIVE",
        "archivo": "glitch_v1.html",
        "precio": 14.99,
        "descripcion": "Shader pro, glitch, delay, echo y 5 figuras 3D"
    },
    "prod_bundle_vj": {
        "nombre": "BUNDLE: Los 3 Visualizadores",
        "archivo": "bundle",  # Especial: no es un solo archivo
        "precio": 29.99,
        "descripcion": "Pack completo con descuento del 30%"
    },
    "sub_pro_mensual": {
        "nombre": "SUSCRIPCIÓN PRO • Acceso a todo + actualizaciones",
        "archivo": "subscription",
        "precio": 7.00,
        "descripcion": "Acceso a todos los visualizadores + versiones nuevas cada mes",
        "tipo": "suscripcion"
    }
}

# Diccionario para guardar descargas autorizadas
# Estructura: {email: {"contrasena": "...", "timestamp": 123, "nombre": "...", "producto_id": "...", "token": "..."}}
descargas_autorizadas = {}

# Diccionario para suscripciones activas (en producción deberías usar una base de datos)
# Estructura: {token_suscripcion: {"email": "...", "expira": timestamp, "activa": True}}
suscripciones_activas = {}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def generar_contrasena(email_cliente):
    """Genera una contraseña única para cada compra"""
    base = f"{email_cliente}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:8].upper()
    extras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NX-{hash_str}{extras}"

def generar_token_suscripcion(email):
    """Genera token único para suscripción"""
    base = f"sub-{email}-{datetime.now().timestamp()}"
    return secrets.token_urlsafe(32)

def verificar_suscripcion(token):
    """Verifica si un token de suscripción es válido y no ha expirado"""
    if token not in suscripciones_activas:
        return None
    suscripcion = suscripciones_activas[token]
    if suscripcion["expira"] < datetime.now().timestamp():
        return None  # Expirada
    return suscripcion

def crear_zip_bundle():
    """Crea un archivo ZIP con los 3 visualizadores y un README"""
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Agregar los 3 visualizadores
        archivos = ["kaleido_v1.html", "ascii_v1.html", "glitch_v1.html"]
        for archivo in archivos:
            ruta = os.path.join("files", archivo)
            if os.path.exists(ruta):
                # Renombrar para mejor presentación
                nombre_destino = {
                    "kaleido_v1.html": "01_NX_KALEIDO_ENGINE.html",
                    "ascii_v1.html": "02_NX_ASCII_ENGINE.html",
                    "glitch_v1.html": "03_NX_GLITCH_ENGINE.html"
                }.get(archivo, archivo)
                zf.write(ruta, nombre_destino)
        
        # Agregar README con instrucciones
        readme_content = """========================================
   NAJARRO X STUDIO - VJ ENGINES
========================================

🎬 ¡Gracias por tu compra!

Este bundle incluye 3 visualizadores en tiempo real:

1. KALEIDO + GRID • GLOW VHS
   - Efectos kaleidoscopio (2/4/8 lados)
   - Grid VHS con scanlines y glitch
   - Control total de colores y partículas

2. ASCII MATRIX • WEBCAM • ORGANIC FLAME
   - ASCII art en tiempo real
   - Mezcla con webcam
   - Partículas de fuego 3D

3. VJ GLITCH ENGINE • AUDIO REACTIVE
   - 5 figuras 3D (toroide, esfera, cubo, pirámide, rombo)
   - Shader psicodélico (4 modos)
   - Efectos: delay, echo, glitch, stroboscópico

========================================
   CÓMO USAR
========================================

1. Descomprime este archivo ZIP
2. Abre cualquier archivo .html en tu navegador
3. Permite el acceso al micrófono cuando lo solicite
4. ¡Conecta tu música y disfruta!

========================================
   MÁS INFORMACIÓN
========================================

Web: https://najarrox.xyz
Instagram: @najarrox
Soporte: soporte@najarrox.xyz

© 2026 NAJARRO X STUDIO - Todos los derechos reservados
"""
        zf.writestr("README_NX_ENGINES.txt", readme_content)
    
    memory_file.seek(0)
    return memory_file

# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook_recurrente():
    """Webhook que recibe Recurrente cuando hay un pago exitoso"""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Webhook sin datos")
            return jsonify({"status": "error"}), 400
        
        event_type = data.get('event_type')
        logger.info(f"📨 Evento recibido: {event_type}")
        
        # ========================================
        # PAGO ÚNICO EXITOSO (producto normal)
        # ========================================
        if event_type == 'payment_intent.succeeded':
            logger.info("✅ Procesando pago único exitoso")
            
            # Extraer datos
            producto_id = data.get('product', {}).get('id')
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            
            # Validaciones
            if not producto_id:
                logger.error("❌ No se encontró ID del producto")
                return jsonify({"status": "error", "message": "No product ID"}), 400
            
            if not email:
                logger.error("❌ No se encontró email del cliente")
                return jsonify({"status": "error", "message": "No email"}), 400
            
            # Verificar que el producto existe
            if producto_id not in PRODUCTOS:
                logger.warning(f"⚠️ Producto no reconocido: {producto_id}")
                return jsonify({"status": "ignored", "reason": "unknown product"}), 200
            
            producto = PRODUCTOS[producto_id]
            logger.info(f"✅ Producto: {producto['nombre']} - Cliente: {nombre} <{email}>")
            
            # Generar token y contraseña
            token = secrets.token_urlsafe(32)
            contrasena = generar_contrasena(email)
            
            # Guardar en el diccionario
            descargas_autorizadas[email] = {
                "contrasena": contrasena,
                "timestamp": datetime.now().timestamp(),
                "nombre": nombre,
                "producto_id": producto_id,
                "token": token
            }
            
            # Generar link de descarga
            link_descarga = f"https://{request.host}/descargar/{token}"
            
            # Enviar email
            exito = enviar_email(email, nombre, contrasena, link_descarga, producto)
            
            if exito:
                logger.info(f"✅ Email enviado a {email}")
                return jsonify({"status": "ok", "message": "Email sent"}), 200
            else:
                logger.error(f"❌ Falló envío a {email}")
                return jsonify({"status": "error", "message": "Email failed"}), 500
        
        # ========================================
        # SUSCRIPCIÓN ACTIVADA
        # ========================================
        elif event_type == 'subscription.active':
            logger.info("🔄 Procesando suscripción activa")
            
            email = data.get('customer', {}).get('email')
            nombre = data.get('customer', {}).get('full_name', 'Cliente')
            
            if not email:
                logger.error("❌ No se encontró email para suscripción")
                return jsonify({"status": "error"}), 400
            
            # Generar token de suscripción
            token_sub = generar_token_suscripcion(email)
            fecha_expiracion = datetime.now().timestamp() + 30 * 24 * 3600  # 30 días
            
            suscripciones_activas[token_sub] = {
                "email": email,
                "nombre": nombre,
                "expira": fecha_expiracion,
                "activa": True
            }
            
            # Enviar email de bienvenida a suscripción
            link_pro = f"https://{request.host}/pro/latest?token={token_sub}"
            
            # Email específico para suscriptores
            html = f"""
            <html>
              <body>
                <h2>🎬 ¡Bienvenido a NX PRO, {nombre}!</h2>
                <p>Tu suscripción mensual está activa. Usa este enlace para descargar todos los visualizadores:</p>
                <a href="{link_pro}">DESCARGAR BUNDLE PRO</a>
                <p>Este enlace es personal y expira en 30 días.</p>
              </body>
            </html>
            """
            
            enviar_email(email, nombre, "SUSCRIPCIÓN PRO", link_pro, PRODUCTOS["sub_pro_mensual"], html_personalizado=html)
            
            return jsonify({"status": "ok", "token": token_sub}), 200
        
        # ========================================
        # SUSCRIPCIÓN CANCELADA
        # ========================================
        elif event_type == 'subscription.canceled':
            logger.info("❌ Suscripción cancelada")
            email = data.get('customer', {}).get('email')
            
            # Buscar y desactivar token
            for token, sub in suscripciones_activas.items():
                if sub["email"] == email:
                    suscripciones_activas[token]["activa"] = False
                    logger.info(f"Suscripción desactivada para {email}")
                    break
            
            return jsonify({"status": "ok"}), 200
        
        # Otros eventos
        logger.info(f"Evento ignorado: {event_type}")
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# ENDPOINTS DE DESCARGA
# ============================================

@app.route('/descargar/<token>')
def descargar_archivo(token):
    """Entrega el archivo físico al cliente validado (descarga única)"""
    # Buscar el token en el diccionario
    email = None
    datos_descarga = None
    
    for mail, datos in descargas_autorizadas.items():
        if datos.get("token") == token:
            email = mail
            datos_descarga = datos
            break
    
    if not email or not datos_descarga:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Error</title><meta http-equiv="refresh" content="3;url=/"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>❌ ENLACE INVÁLIDO</h2>
                <p>El enlace que usaste no es válido o ya expiró.</p>
                <p>Redirigiendo...</p>
            </div>
        </body>
        </html>
        ''', 404
    
    # Verificar expiración (7 días)
    if datetime.now().timestamp() - datos_descarga["timestamp"] > 7 * 24 * 3600:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Expirado</title><meta http-equiv="refresh" content="3;url=/"></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>⏰ ENLACE EXPIRADO</h2>
                <p>Este enlace expiró después de 7 días.</p>
                <p>Contacta a soporte@najarrox.xyz</p>
            </div>
        </body>
        </html>
        ''', 403
    
    producto_id = datos_descarga["producto_id"]
    producto = PRODUCTOS.get(producto_id)
    
    if not producto:
        abort(404, "Producto no encontrado")
    
    # Caso especial: BUNDLE
    if producto_id == "prod_bundle_vj":
        zip_file = crear_zip_bundle()
        return send_file(
            zip_file,
            as_attachment=True,
            download_name=f"NX_BUNDLE_{datetime.now().strftime('%Y%m%d')}.zip",
            mimetype="application/zip"
        )
    
    # Producto normal: archivo individual
    ruta_archivo = os.path.join("files", producto["archivo"])
    
    if not os.path.exists(ruta_archivo):
        logger.error(f"Archivo no encontrado: {ruta_archivo}")
        abort(404, "Archivo no encontrado")
    
    # Opcional: eliminar el token después de la primera descarga (descarga única)
    # del descargas_autorizadas[email]["token"]
    
    return send_file(
        ruta_archivo,
        as_attachment=True,
        download_name=f"NX_{producto_id}_{datetime.now().strftime('%Y%m%d')}.html",
        mimetype="text/html"
    )

@app.route('/pro/latest')
def pro_download():
    """Endpoint para suscriptores PRO - siempre sirve la última versión"""
    token = request.args.get('token')
    
    if not token:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Acceso Pro</title></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #00c853; max-width:400px; margin:auto;">
                <h2>🔐 ACCESO PRO</h2>
                <p>Este endpoint requiere un token de suscripción válido.</p>
                <p>Si eres suscriptor, revisa tu email.</p>
                <a href="/" style="color:#00c853;">Volver al inicio</a>
            </div>
        </body>
        </html>
        ''', 403
    
    suscripcion = verificar_suscripcion(token)
    
    if not suscripcion or not suscripcion["activa"]:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Suscripción Inválida</title></head>
        <body style="background:#0a0a0a; color:white; font-family:monospace; text-align:center; padding-top:50px;">
            <div style="background:#1a1a1a; padding:30px; border:3px solid #ff4444; max-width:400px; margin:auto;">
                <h2>⚠️ SUSCRIPCIÓN EXPIRADA</h2>
                <p>Tu suscripción no está activa o ha expirado.</p>
                <p>Renueva en <a href="https://najarrox.xyz">najarrox.xyz</a></p>
            </div>
        </body>
        </html>
        ''', 403
    
    # Crear bundle actualizado con las últimas versiones
    zip_file = crear_zip_bundle()
    
    return send_file(
        zip_file,
        as_attachment=True,
        download_name=f"NX_PRO_{datetime.now().strftime('%Y%m%d')}.zip",
        mimetype="application/zip"
    )

# ============================================
# ENDPOINTS DE DEMO Y PÁGINAS PÚBLICAS
# ============================================

@app.route('/demo/kaleido')
def demo_kaleido():
    """Demo gratuita del visualizador Kaleido (con marca de agua/tiempo limitado)"""
    ruta = os.path.join("files", "kaleido_v1.html")
    if not os.path.exists(ruta):
        return "Demo no disponible", 404
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Inyectar código de demo (marca de agua que aparece cada 60 segundos)
    demo_script = """
    <script>
    // DEMO MODE - Marca de agua Najarro X
    (function() {
        let tiempoInicio = Date.now();
        let overlayCreado = false;
        
        function mostrarOverlay() {
            if (overlayCreado) return;
            const div = document.createElement('div');
            div.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: rgba(0,0,0,0.8);
                color: #00ff41;
                font-family: monospace;
                padding: 8px 16px;
                z-index: 9999;
                border-left: 3px solid #00ff41;
                font-size: 12px;
                pointer-events: none;
            `;
            div.innerHTML = '🔴 DEMO - Compra en najarrox.xyz 🔴';
            document.body.appendChild(div);
            overlayCreado = true;
        }
        
        function verificarDemo() {
            const tiempoTranscurrido = (Date.now() - tiempoInicio) / 1000;
            if (tiempoTranscurrido > 60 && !overlayCreado) {
                mostrarOverlay();
            }
            if (tiempoTranscurrido > 120) {
                // Opcional: pausar o desenfocar después de 2 minutos
                const blocker = document.createElement('div');
                blocker.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.95);
                    z-index: 10000;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: monospace;
                    color: #ff00ff;
                    font-size: 24px;
                    text-align: center;
                `;
                blocker.innerHTML = '<div><h1>⏰ DEMO FINALIZADA</h1><p>Compra la versión completa en<br><a href="https://najarrox.xyz" style="color:#00ff41;">najarrox.xyz</a></p></div>';
                document.body.appendChild(blocker);
            }
        }
        
        setInterval(verificarDemo, 1000);
    })();
    </script>
    """
    
    # Insertar antes de </body>
    contenido = contenido.replace('</body>', demo_script + '</body>')
    
    return contenido, 200, {'Content-Type': 'text/html'}

@app.route('/')
def home():
    """Página principal del servidor"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NAJARRO X STUDIO - VJ Engines</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Courier New', monospace;
                background: #0a0a0a;
                color: white;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            .card {
                background: #1a1a1a;
                border: 2px solid #8b5cf6;
                padding: 40px;
                margin-bottom: 20px;
                text-align: center;
            }
            h1 {
                font-size: 2rem;
                border-left: 8px solid #8b5cf6;
                padding-left: 20px;
                margin-bottom: 20px;
            }
            .status {
                color: #00c853;
                font-weight: bold;
            }
            .productos {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 30px;
            }
            .producto {
                background: #0a0a0a;
                border: 1px solid #333;
                padding: 20px;
                flex: 1;
                min-width: 200px;
            }
            .producto h3 {
                color: #8b5cf6;
                margin-bottom: 10px;
            }
            .precio {
                font-size: 1.5rem;
                color: #00c853;
                margin: 10px 0;
            }
            .demo {
                color: #ffaa44;
                text-decoration: none;
                font-size: 12px;
            }
            footer {
                margin-top: 40px;
                text-align: center;
                color: #555;
                font-size: 11px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>🚀 NAJARRO X STUDIO</h1>
                <p class="status">✅ SISTEMA DE DISTRIBUCIÓN ACTIVO</p>
                <p>Servidor alojado en Render • Webhook conectado a Recurrente</p>
                <p>🔒 Descargas protegidas con token único</p>
            </div>
            
            <div class="productos">
                <div class="producto">
                    <h3>🌀 KALEIDO + GRID</h3>
                    <p>Visual psicodélico con glow VHS</p>
                    <div class="precio">$9.99 USD</div>
                    <a href="/demo/kaleido" class="demo">🎬 Probar Demo</a>
                </div>
                <div class="producto">
                    <h3>🔥 ASCII WEBCAM</h3>
                    <p>ASCII art + fuego + cámara</p>
                    <div class="precio">$12.99 USD</div>
                    <span class="demo">Demo pronto</span>
                </div>
                <div class="producto">
                    <h3>🎛️ GLITCH PRO</h3>
                    <p>Shader pro, 5 figuras 3D</p>
                    <div class="precio">$14.99 USD</div>
                    <span class="demo">Demo pronto</span>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h2>🎯 COMPRAR</h2>
                <p>Visita <strong><a href="https://najarrox.xyz" style="color:#8b5cf6;">najarrox.xyz</a></strong> para adquirir tu licencia</p>
                <p style="margin-top: 10px; font-size: 12px;">📊 Estado: <span class="status">Online</span> | Descargas activas: ''' + str(len(descargas_autorizadas)) + '''</p>
            </div>
            
            <footer>
                NAJARRO X ESTUDIO · Panamá 2026 · SOPORTE: soporte@najarrox.xyz
            </footer>
        </div>
    </body>
    </html>
    '''

@app.route('/status')
def status():
    """Endpoint de estado para monitoreo"""
    return jsonify({
        "status": "activo",
        "productos_disponibles": list(PRODUCTOS.keys()),
        "descargas_activas": len(descargas_autorizadas),
        "suscripciones_activas": len(suscripciones_activas),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "servidor": "Render.com",
        "version": "2.0-multiproducto"
    })

@app.route('/health')
def health():
    """Health check para Render"""
    return "OK", 200

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Servidor NX Studio iniciado en puerto {port}")
    logger.info(f"📦 Productos configurados: {list(PRODUCTOS.keys())}")
    app.run(host='0.0.0.0', port=port, debug=False)