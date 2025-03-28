import os
import json
import re
from flask import Flask, Blueprint, render_template, request, jsonify, session, redirect, url_for
import openai
from dotenv import load_dotenv
from flask_session import Session

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)

# Configurar la API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar la sesión
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Obtener la ruta absoluta del archivo 8vo_curso.json
data_path = os.path.join(os.path.dirname(__file__), '8vo_curso.json')

# Cargar datos desde 8vo_curso.json
try:
    with open(data_path, 'r') as f:
        data = json.load(f)
        if not isinstance(data, dict) or 'estudiantes' not in data:
            raise ValueError("El archivo JSON no tiene el formato esperado.")
        data = data['estudiantes']
        print(f"Datos cargados correctamente: {len(data)} registros encontrados.")
except (FileNotFoundError, ValueError) as e:
    print(f"Error: {e}")
    data = []

# Rutas
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

@main.route('/faq')
def documentacion():
    return render_template('faq.html')

@main.route('/faq')
def contacto():
    return render_template('faq.html')

@main.route('/faq')
def logout():
    session.clear()
    return redirect(url_for('main.home'))  # Te redirige al home después del logout



@main.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    response = get_response(user_message)
    return jsonify({"bot_message": response})

# Función principal de respuesta
def get_response(message):
    message = message.lower().strip()

    # Cancelar proceso
    if "cancelar" in message:
        session['step'] = 0
        session['cedula'] = None
        session['unidad'] = None
        return "✅ El proceso fue cancelado. ¿En qué puedo ayudarte ahora?"

    # Iniciar proceso de calificaciones
    if any(word in message for word in ["calificaciones", "notas"]):
        session['cedula'] = None
        session['unidad'] = None
        session['step'] = 1
        return "Por favor, proporciona tu número de cédula (10 dígitos)."

    # Paso 1: Esperando cédula
    if session.get('step') == 1:
        if re.match(r"^\d{10}$", message):
            session['cedula'] = message
            session['step'] = 2
            return "Gracias. Ahora, dime la unidad que deseas consultar (Ejemplo: UNIDAD1)."
        else:
            # Detectar si no es cédula pero parece una pregunta general
            if not re.search(r"\d{5,}", message):
                session['step'] = 0
                return responder_pregunta_general(message)
            return "El número de cédula debe contener solo 10 dígitos. Inténtalo de nuevo."

    # Paso 2: Esperando unidad
    if session.get('step') == 2:
        unidad = f'UNIDAD{message}' if not message.upper().startswith('UNIDAD') else message.upper()
        session['unidad'] = unidad
        session['step'] = 0
        return buscar_calificaciones(session['cedula'], unidad)

    # Fuera del flujo: usar GPT
    return responder_pregunta_general(message)

# Buscar calificaciones en JSON
def buscar_calificaciones(cedula, unidad):
    for estudiante in data:
        if estudiante["id"] == cedula and estudiante["unidad"].upper() == unidad:
            return f"✅ Hola {estudiante['nombre']}, aquí tienes tus calificaciones: <a href='{estudiante['enlace']}' target='_blank' style='color: blue;'>Ver calificaciones</a>"
    return f"❌ No se encontraron calificaciones para la cédula {cedula} y la unidad {unidad}."

# GPT para preguntas generales
def responder_pregunta_general(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres RASGAEL, un asistente educativo que responde preguntas claras y precisas sobre cualquier tema, incluyendo consultas académicas."},
                {"role": "user", "content": message}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("Error GPT:", e)
        return "Lo siento, hubo un error al generar la respuesta. Intenta de nuevo."

# Registrar el blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
