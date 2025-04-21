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
# CRED_PATH = os.path.join(os.path.dirname(__file__), 'credenciales_google.json')
CRED_PATH = '/etc/secrets/GOOGLE_APPLICATION_CREDENTIALS'

# Conectar con Google Sheets
def obtener_hoja_service():
    creds = service_account.Credentials.from_service_account_file(
        CRED_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet

# Leer datos de campañas
def obtener_campanas():
    sheet = obtener_hoja_service()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGO_CAMPANAS).execute()
    valores = result.get('values', [])
    
    campanas = []
    for fila in valores:
        if len(fila) >= 11:
            campanas.append({
                "cliente": fila[0],
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

    # Buscar primero en los datos de campañas
    respuesta_campanas = responder_info_campanas(message)
    if respuesta_campanas:
        return respuesta_campanas

    # Si no encontró nada, responde con el modelo GPT
    return responder_pregunta_general(message)

# FUNCIONES

def responder_info_campanas(message):
    campanas = obtener_campanas()

    if "clientes" in message:
        clientes = [c['cliente'] for c in campanas]
        clientes_str = ' - '.join(sorted(set(clientes)))
        return f"🗒️ Clientes actuales: - {clientes_str}"

    if "mayor alcance" in message:
        mayor = max(campanas, key=lambda x: int(x['alcance']))
        session['ultimo_cliente'] = mayor['cliente']
        return f"📈 Mayor alcance: {mayor['cliente']} ({mayor['alcance']} personas)"

    if any(palabra in message for palabra in ["inversion", "inversión"]):
        ultimo_cliente = session.get('ultimo_cliente')
        if ultimo_cliente:
            for campana in campanas:
                if campana['cliente'].lower() == ultimo_cliente.lower():
                    return f"💵 Inversión de {campana['cliente']}: {campana['inversion']}"
            return "⚠️ No encontré el dato de inversión del último cliente mencionado."
        else:
            return "⚠️ No tengo un cliente reciente para buscar la inversión. Por favor, especifica el nombre."

    for campana in campanas:
        cliente = campana['cliente'].lower()
        if cliente in message:
            session['ultimo_cliente'] = cliente
            respuesta = ""
            if "inversion" in message or "inversión" in message:
                respuesta += f"💰 Inversión: {campana['inversion']}\n"
            if "alcance" in message:
                respuesta += f"📈 Alcance: {campana['alcance']} personas\n"
            if "interacciones" in message:
                respuesta += f"🗨️ Interacciones: {campana['interacciones']}\n"
            if "segmentación" in message or "segmentacion" in message:
                respuesta += f"🎯 Segmentación: {campana['segmentacion']}\n"
            if "formato" in message or "formato creativo" in message:
                respuesta += f"🖼️ Formato creativo: {campana['formato_creativo']}\n"
            if "fecha" in message:
                respuesta += f"📅 Desde {campana['fecha_inicio']} hasta {campana['fecha_fin']}\n"

            if respuesta:
                return respuesta.strip()

    return None

def responder_pregunta_general(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres FARUM, un asistente especializado en marketing digital, campañas de publicidad y asesoría comercial. Si el usuario menciona campañas o clientes, debes responder pidiendo más detalles si no son claros."},
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
