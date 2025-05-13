import os
import json
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

# 📊 Configuración de Google Sheets
SHEET_ID = "1LvDxCBZuACJZffyVB7mAYYoYpqHQA7D4a6peYq8qMSo"
# CRED_PATH = os.path.join(os.path.dirname(__file__), 'credenciales_google.json')
CRED_PATH = '/etc/secrets/GOOGLE_APPLICATION_CREDENTIALS'

RANGO_CLIENTES = "CLIENTES!A1:D"
RANGO_CAMPANAS = "CAMPANAS!A1:F"
RANGO_CONSOLIDADO = "CONSOLIDADO!A1:K"

def obtener_hoja_service():
    creds = service_account.Credentials.from_service_account_file(
        CRED_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def leer_hoja_como_dict(rango):
    sheet = obtener_hoja_service()
    valores = sheet.values().get(spreadsheetId=SHEET_ID, range=rango).execute().get('values', [])
    if not valores:
        return []
    encabezado = valores[0]
    return [dict(zip(encabezado, fila + [""] * (len(encabezado) - len(fila)))) for fila in valores[1:]]

def cargar_datos():
    return {
        "CLIENTES": leer_hoja_como_dict(RANGO_CLIENTES),
        "CAMPANAS": leer_hoja_como_dict(RANGO_CAMPANAS),
        "CONSOLIDADO": leer_hoja_como_dict(RANGO_CONSOLIDADO)
    }

# 🌐 Rutas principales
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

# 🧠 Endpoint del chatbot
@main.route('/send_message', methods=['POST'])
def send_message():
    data_json = request.get_json()
    user_message = data_json.get('message')
    auto = data_json.get('auto', False)

    if not auto:
        print(f"🟣 Usuario: {user_message}")

    datos = cargar_datos()
    response = get_response(user_message, datos)
    return jsonify({"bot_message": response})

def get_response(message, datos):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres FARUM, un asistente especializado en marketing, campañas y análisis comercial. "
                        "A continuación se te proporciona información real desde tres hojas de cálculo. "
                        "Usa estos datos para responder de manera útil, comparativa y natural:"
                        "Si el usuario pide rankings, análisis o comparativas, responde con listados claros, sugerencias y un lenguaje profesional pero accesible:"
                        f"\n\nCLIENTES:\n{json.dumps(datos['CLIENTES'], indent=2)}"
                        f"\n\nCAMPANAS:\n{json.dumps(datos['CAMPANAS'], indent=2)}"
                        f"\n\nCONSOLIDADO:\n{json.dumps(datos['CONSOLIDADO'], indent=2)}"
                    )
                },
                {"role": "user", "content": message}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("❌ Error GPT:", e)
        return "⚠️ Hubo un error al generar la respuesta. Revisa la terminal."

# Registrar el blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
