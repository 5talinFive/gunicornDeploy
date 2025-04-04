import os
import json
import re
import io
import difflib
from flask import Flask, Blueprint, render_template, request, jsonify, session, redirect, url_for
import openai
from dotenv import load_dotenv
from flask_session import Session
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuración de Google Sheets
SHEET_ID = "16_q09WPajV5ju5vyQlufRyq3mibZ6ADVIsRh3oILlrQ"
RANGO_INFO = "INFORG!A2:B"
RANGO_NOTAS = "CALIFICACIONESINTENSIVO!A2:C"
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

# Leer calificaciones
def obtener_calificaciones_desde_sheets():
    sheet = obtener_hoja_service()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGO_NOTAS).execute()
    return result.get('values', [])

# Leer información institucional
def obtener_informacion_general():
    sheet = obtener_hoja_service()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGO_INFO).execute()
    valores = result.get('values', [])
    return {fila[0].strip().lower(): fila[1].strip() for fila in valores if len(fila) >= 2}

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

    if "cancelar" in message:
        session['step'] = 0
        session['cedula'] = None
        session['unidad'] = None
        return "✅ El proceso fue cancelado. ¿En qué puedo ayudarte ahora?"

    if any(palabra in message for palabra in ["notas", "calificaciones"]):
        session['step'] = 1
        session['cedula'] = None
        session['unidad'] = None
        return "Por favor, proporciona tu número de cédula (10 dígitos)."

    if session.get('step') == 1:
        if re.match(r"^\d{10}$", message):
            session['cedula'] = message.strip()
            session['step'] = 2
            return "Gracias. Ahora, dime la unidad que deseas consultar (Ejemplo: UNIDAD1)."
        else:
            if not re.search(r"\d{5,}", message):
                session['step'] = 0
                return responder_info_colegio(message) or responder_pregunta_general(message)
            return "❌ El número de cédula debe contener solo 10 dígitos. Inténtalo de nuevo."

    if session.get('step') == 2:
        if not re.search(r'\d', message):
            session['step'] = 0
            return "❌ Unidad inválida. Debe ser algo como UNIDAD1. Intenta de nuevo."
        unidad = f"UNIDAD{message}" if not message.upper().startswith("UNIDAD") else message.upper()
        session['unidad'] = unidad
        session['step'] = 0
        return buscar_calificaciones(session['cedula'], unidad)

    # 🔍 Buscar información institucional
    respuesta_info = responder_info_colegio(message)
    if respuesta_info:
        return respuesta_info

    # 💬 Si no se encuentra nada, usar modelo
    return responder_pregunta_general(message)

# Buscar en calificaciones
def buscar_calificaciones(cedula, unidad):
    if not cedula or not unidad:
        return "❌ Faltan datos para buscar las calificaciones."

    filas = obtener_calificaciones_desde_sheets()

    cedula = cedula.strip()
    unidad = unidad.strip().upper()

    print("📄 Calificaciones cargadas:")
    for fila in filas:
        print(fila)

    for fila in filas:
        if len(fila) >= 3:
            cedula_fila = fila[1].strip()
            unidad_fila = fila[2].strip().upper()
            if cedula_fila == cedula and unidad_fila == unidad:
                return f"✅ Aquí tienes tus calificaciones: <a href='{fila[0]}' target='_blank' style='color: #7e5bef;'>Ver calificaciones</a>"

    return f"❌ No se encontraron calificaciones para la cédula {cedula} y la unidad {unidad}."

# Buscar mejor coincidencia institucional
def responder_info_colegio(message):
    datos = obtener_informacion_general()
    message_lower = message.lower()
    claves = list(datos.keys())
    coincidencia = difflib.get_close_matches(message_lower, claves, n=1, cutoff=0.6)

    if coincidencia:
        return f"🏫 {datos[coincidencia[0]]}"

    if any(palabra in message_lower for palabra in ["colegio", "rafael galeth", "institución", "quiénes son"]):
        return "🏫 El Colegio Rafael Galeth es una institución educativa que ofrece formación virtual intensiva en distintos niveles. Si deseas conocer requisitos, matrículas o calificaciones, ¡solo pregúntame!"

    return None

# Chat IA con GPT
def responder_pregunta_general(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Eres RASGAEL, un asistente educativo útil y amable. Si no tienes datos del Colegio Rafael Galeth, responde con base en tu conocimiento general."
                },
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
