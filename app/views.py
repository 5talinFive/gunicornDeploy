from flask import Flask, Blueprint, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)

# Configurar la API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Historial de conversación (inicia vacío)
messages = []

@main.route('/')
def index():
    return render_template('index.html', messages=messages)

@main.route('/send_message', methods=['POST'])
def send_message():
    print("Recibiendo datos del usuario...")

    # Recibir mensaje como JSON
    data = request.get_json()
    user_message = data.get("message", "").strip()

    print(f"Mensaje recibido: {user_message}")

    if not user_message:  # Evita mensajes vacíos
        return jsonify({'bot_message': "Por favor, escribe un mensaje válido."})

    # Agregar mensaje del sistema solo al inicio
    if len(messages) == 0:
        messages.append({
            "role": "system",
            "content": (
                "Presentate como Rasgael, el asistente virtual del colegio Rafael Galeth. "
                "Responde de manera clara, concisa y precisa. "
                "Solo responde la pregunta sin hacer preguntas adicionales."
            )
        })

    # Agregar el mensaje del usuario al historial
    messages.append({'role': 'user', 'content': user_message})

    try:
        # Llamar a la API de OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0  # Respuestas más precisas
        )

        # Extraer la respuesta del asistente
        bot_message = response['choices'][0]['message']['content'].strip()

        print(f"Respuesta de OpenAI: {bot_message}")

        # Agregar la respuesta al historial
        messages.append({'role': 'assistant', 'content': bot_message})

    except Exception as e:
        bot_message = "Lo siento, hubo un error al procesar tu mensaje."
        print("Error en OpenAI:", str(e))

    return jsonify({'bot_message': bot_message})

app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
