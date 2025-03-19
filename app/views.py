from flask import Flask, Blueprint, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv
from app.calificaciones import obtener_informacion_estudiante  # Importar la función

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)

# Configurar la API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Mensaje de sistema para definir el comportamiento del asistente
system_message = {
    "role": "system",
    "content": "Eres un asistente virtual llamado Rasgael. Tu función principal es ayudar a los estudiantes a consultar su información. Si el usuario proporciona un número de cédula, debes buscar la información en la base de datos .json y devolver su nombre y enlace."
}

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({'bot_message': "Por favor, escribe un mensaje válido."})

        # Inicializar mensajes con el mensaje del sistema
        messages = [system_message]

        if any(word in user_message.lower() for word in ["calificaciones", "informacion"]):
            palabras = user_message.split()
            cedula = next((p for p in palabras if p.isdigit()), None)

            if cedula:
                nombre, enlace = obtener_informacion_estudiante(cedula, "8vo_curso")

                if nombre and enlace:
                    bot_message = f"Hola {nombre}, aquí está tu enlace: <a href='{enlace}' target='_blank' style='color: blue;'>Enlace</a>"
                else:
                    bot_message = f"❌ No se encontró el estudiante con cédula {cedula}."

                return jsonify({'bot_message': bot_message})

        # Agregar el mensaje del usuario a la conversación
        messages.append({'role': 'user', 'content': user_message})

        # Llamar a la API de OpenAI para obtener la respuesta del asistente
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )
        bot_message = response['choices'][0]['message']['content'].strip()

        # Evitar repetir el saludo si el usuario está finalizando la interacción
        if user_message.lower() in ["gracias", "adios", "hasta luego"]:
            bot_message = "¡De nada! Si necesitas más ayuda, no dudes en volver. ¡Que tengas un buen día!"

        # Agregar la respuesta del asistente a la conversación
        messages.append({'role': 'assistant', 'content': bot_message})

        return jsonify({'bot_message': bot_message})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'bot_message': "Lo siento, hubo un error al procesar tu mensaje."}), 500

app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
