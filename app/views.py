import os
import json
from openai import OpenAI
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

@main.route('/generador-imagenes')
def imagenes():
    return render_template('image-generation.html')


# Ruta oara generar imagenes con DALL-E 
@main.route('/generar_imagen', methods=['POST'])
def generar_imagen():
    from flask import request, jsonify

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    datos = request.json
    nombre_cliente = datos.get("nombre_cliente", "Cliente")
    ciudad = datos.get("ciudad", "Ciudad")
    # plataforma = datos.get("plataforma", "Plataforma")
    antecedente = datos.get("antecedente", "Sin descripción disponible")
    prompt_extra = datos.get("prompt_extra", "")


    prompt = f"Logo moderno para {nombre_cliente} de {ciudad}, que represente y trasmita su {antecedente}, profesional. {prompt_extra} "

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url
        return jsonify({"imagen_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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


# @main.route('/generador-imagenes')
# def imagenes():
#     return render_template('image-generation.html')


@main.route('/get_clientes', methods=['GET'])
def get_clientes():
    datos = cargar_datos()
    print("🔎 Primer registro de CLIENTES:", datos["CLIENTES"][0])  # solo para verificar
    clientes = [fila["Nombre Cliente"] for fila in datos["CLIENTES"]]  # ¡Nombre de la la columna Nombre Cliente, hoja CLIENTES!
    return jsonify({"clientes": clientes})


# obtiene info del cliente, antecedentes e imagenes
@main.route('/get_info_cliente', methods=['POST'])
def get_info_cliente():
    cliente = request.json.get("cliente")
    datos = cargar_datos()

    for fila in datos["CLIENTES"]:
        if fila.get("Nombre Cliente") == cliente:
            return jsonify({
                "imagen": fila.get("Imagen", ""),
                "antecedente": fila.get("Antecedente", "")
            })

    return jsonify({"error": "Cliente no encontrado"}), 404




#Endpoint del chatbot
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
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres FARUM, un asistente especializado en marketing, campañas y análisis comercial. "
                        "A continuación se te proporciona información real desde tres hojas de cálculo. "
                        "Usa estos datos para responder de manera útil, comparativa y natural. "
                        "Si el usuario pide rankings, análisis o comparativas, responde con listados claros, sugerencias y un lenguaje profesional pero accesible:"
                        f"\n\nCLIENTES:\n{json.dumps(datos['CLIENTES'], indent=2)}"
                        f"\n\nCAMPANAS:\n{json.dumps(datos['CAMPANAS'], indent=2)}"
                        f"\n\nCONSOLIDADO:\n{json.dumps(datos['CONSOLIDADO'], indent=2)}"
                    )
                },
                {"role": "user", "content": message}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        print("❌ Error GPT:", e)
        return "⚠️ Hubo un error al generar la respuesta. Revisa la terminal."


# Registrar el blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
