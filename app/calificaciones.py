import json
import os

def obtener_calificaciones(cedula_buscada, curso):
    # Obtener la ruta del archivo JSON dentro de la carpeta "app"
    ruta_base = os.path.dirname(os.path.abspath(__file__))  # Ruta de "calificaciones.py"
    ruta_json = os.path.join(ruta_base, f"{curso}.json")  # Se une la ruta de la carpeta "app"

    # Cargar los datos del JSON
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)["estudiantes"]

    estudiante = next((e for e in data if e["id"] == cedula_buscada), None)
    return estudiante

def obtener_informacion_estudiante(cedula, unidad):
    estudiante = obtener_calificaciones(cedula, "8vo_curso")
    if estudiante:
        if estudiante['unidad'].lower() == unidad.lower():
            return estudiante['nombre'], estudiante['enlace']
    return None, None
