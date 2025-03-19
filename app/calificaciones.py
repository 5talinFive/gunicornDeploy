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

    if estudiante:
        calificaciones = estudiante["calificaciones"]
        # Convertir las calificaciones a números
        calificaciones_numericas = {k: float(v.replace(",", ".")) for k, v in calificaciones.items()}
        calificacion_final = sum(calificaciones_numericas.values()) / len(calificaciones_numericas)
        return calificacion_final, calificaciones_numericas
    else:
        return None, None

def obtener_informacion_estudiante(cedula_buscada, curso):
    # Obtener la ruta del archivo JSON dentro de la carpeta "app"
    ruta_base = os.path.dirname(os.path.abspath(__file__))  # Ruta de "calificaciones.py"
    ruta_json = os.path.join(ruta_base, f"{curso}.json")  # Se une la ruta de la carpeta "app"

    # Cargar los datos del JSON
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)["estudiantes"]

    estudiante = next((e for e in data if e["id"] == cedula_buscada), None)

    if estudiante:
        nombre = estudiante["nombre"]
        enlace = estudiante["enlace"]
        return nombre, enlace
    else:
        return None, None
