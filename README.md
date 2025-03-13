# Flask Chat Application

This is a simple chat application built using Flask and Gunicorn. It allows users to send and receive messages in a chat interface, similar to a ChatGPT interface.

## Project Structure

```
flask-chat-app
├── app
│   ├── __init__.py
│   ├── views.py
│   ├── static
│   │   └── styles.css
│   └── templates
│       └── chat.html
├── run.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd flask-chat-app
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run the application using Gunicorn, execute the following command:

```bash
gunicorn run:app
```

The application will be accessible at `http://127.0.0.1:8000`.

## Usage

Once the application is running, open your web browser and navigate to `http://127.0.0.1:8000`. You will see the chat interface where you can send and receive messages.

## Contributing

Feel free to submit issues or pull requests if you would like to contribute to this project.