from flask import Flask, Blueprint, render_template, request, redirect, url_for

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    
    # Register blueprints
    from .views import main
    app.register_blueprint(main)

    return app