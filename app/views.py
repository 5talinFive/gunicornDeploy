import os
import json
from flask import Flask, Blueprint, render_template, request, jsonify, session, redirect, url_for
import openai
from dotenv import load_dotenv
from flask_session import Session
from google.oauth2 import service_account
from googleapiclient.discovery import build
import difflib

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuración de Google Sheets
SHEET_ID = "1LvDxCBZuACJZffyVB7mAYYoYpqHQA7D4a6peYq8qMSo"
RANGO_CAMPANAS = "CAMPANAS!A2:K"
RANGO_CLIENTES = "CLIENTES!A2:D"
CRED_PATH = os.path.join(os.path.dirname(__file__), 'credenciales_google.json')

# Conectar con Google Sheets
def obtener_hoja_service():
    creds = service_account.Credentials.from_service_account_file(
        CRED_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

# Leer hoja CLIENTES
def obtener_clientes():
    sheet = obtener_hoja_service()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGO_CLIENTES).execute()
    valores = result.get('values', [])

    clientes = []
    for fila in valores:
        if len(fila) >= 4:
            clientes.append({
                "id": fila[0],
                "nombre": fila[1],
                "ciudad": fila[2],
                "plataforma": fila[3]
            })
    return clientes

# Leer hoja CAMPANAS
def obtener_campanas():
    sheet = obtener_hoja_service()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGO_CAMPANAS).execute()
    valores = result.get('values', [])

    campanas = []
    for fila in valores:
        if len(fila) >= 11:
            campanas.append({
                "cliente": fila[0],  # ID del cliente
                "campana": fila[1],
                "plataforma": fila[2],
                "ciudad": fila[3],
                "inversion": fila[4],
                "alcance": fila[5],
                "interacciones": fila[6],
                "segmentacion": fila[7],
                "formato_creativo": fila[8],
                "fecha_inicio": fila[9],
                "fecha_fin": fila[10]
            })
    return campanas

# Combinar campañas con nombres reales
def campañas_con_nombres():
    campanas = obtener_campanas()
    clientes = obtener_clientes()

    mapa_clientes = {c['id']: c['nombre'] for c in clientes}

    for c in campanas:
        id_cliente = c['cliente']
        c['cliente'] = mapa_clientes.get(id_cliente, f"ID {id_cliente}")

    return campanas

# RUTAS
@main.route('/')
def home():
    return render_template('index.html')

@main.route('/informacion')
def informacion():
    return render_template('informacion.html')

@main.route('/chat')
def chat():
    return render_template('iahome.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/documentacion')
def documentacion():
    return render_template('faq.html')

@main.route('/contacto')
def contacto():
    return render_template('faq.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

# FLUJO PRINCIPAL
@main.route('/send_message', methods=['POST'])
def send_message():
    data_json = request.get_json()
    user_message = data_json.get('message')
    auto = data_json.get('auto', False)

    if not auto:
        print(f"🟣 Usuario: {user_message}")

    response = get_response(user_message)
    return jsonify({"bot_message": response})

def get_response(message):
    message = message.strip().lower()
    respuesta_campanas = responder_info_campanas(message)
    if respuesta_campanas:
        return respuesta_campanas
    return responder_pregunta_general(message)

def responder_info_campanas(message):
    campanas = campañas_con_nombres()

    if "clientes" in message:
        clientes = obtener_clientes()
        lista = sorted(set(c['nombre'] for c in clientes))
        return "🗒️ Clientes actuales:\n- " + "\n- ".join(lista)

    if any(palabra in message for palabra in [
        "total de inversion", "suma de inversion", "suma total", "total inversión",
        "inversion total", "dame el total de inversion", "cuánto se invirtió"
    ]):
        total = 0
        detalles = []
        for c in campanas:
            try:
                monto = float(c['inversion'].replace('$', '').replace(',', '').strip())
                total += monto
                detalles.append(f"{c['cliente']}: ${monto:,.2f}")
            except:
                continue
        respuesta = "💰 Inversión por cliente:\n" + "\n".join(detalles)
        respuesta += f"\n\n🔢 Inversión total: ${total:,.2f}"
        return respuesta

    if "menos se invirtió" in message or "invirtió menos" in message or "menor inversión" in message:
        min_cliente = None
        min_valor = float('inf')
        for c in campanas:
            try:
                monto = float(c['inversion'].replace('$', '').replace(',', '').strip())
                if monto < min_valor:
                    min_valor = monto
                    min_cliente = c['cliente']
            except:
                continue
        if min_cliente:
            return f"📉 El cliente con menor inversión es **{min_cliente}** con ${min_valor:,.2f}"
        else:
            return "⚠️ No pude determinar el cliente con menor inversión por un error en los datos."

    if "comparativa" in message or ("alcance" in message and "cliente" in message):
        comparativa = {}
        for c in campanas:
            try:
                comparativa.setdefault(c['cliente'], 0)
                comparativa[c['cliente']] += int(c['alcance'].replace(',', ''))
            except:
                continue
        ordenado = sorted(comparativa.items(), key=lambda x: x[1], reverse=True)
        comparacion = [f"{cliente}: {alcance:,} personas" for cliente, alcance in ordenado]
        return "📊 Comparativa de alcances por cliente:\n" + "\n".join(comparacion)

    for campana in campanas:
        cliente = campana['cliente'].lower()
        if cliente in message:
            session['ultimo_cliente'] = cliente
            respuesta = [f"📌 Información de {campana['cliente']}:"]

            if "inversion" in message or "inversión" in message:
                respuesta.append(f"💰 Inversión: {campana['inversion']}")
            if "alcance" in message:
                respuesta.append(f"📈 Alcance: {campana['alcance']} personas")
            if "interacciones" in message:
                respuesta.append(f"🗨️ Interacciones: {campana['interacciones']}")
            if "segmentación" in message or "segmentacion" in message:
                respuesta.append(f"🎯 Segmentación: {campana['segmentacion']}")
            if "formato" in message:
                respuesta.append(f"🖼️ Formato creativo: {campana['formato_creativo']}")
            if "fecha" in message:
                respuesta.append(f"📅 Desde {campana['fecha_inicio']} hasta {campana['fecha_fin']}")

            return "\n".join(respuesta)

    return None

def responder_pregunta_general(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres FARUM, un asistente especializado en marketing digital, campañas de publicidad y asesoría comercial. Si el usuario menciona campañas o clientes, responde de forma natural y analiza los datos disponibles."},
                {"role": "user", "content": message}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("❌ Error GPT:", e)
        return "⚠️ Lo siento, hubo un problema al generar la respuesta."

# Registrar blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
