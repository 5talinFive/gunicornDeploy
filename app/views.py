from flask import Flask, Blueprint, render_template, request, redirect, url_for

app = Flask(__name__)

main = Blueprint('main', __name__)

messages = []

@main.route('/')
def index():
    return render_template('index.html', messages=messages)

@main.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    messages.append({'sender': 'You', 'text': message})
    return redirect(url_for('main.index'))

app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)