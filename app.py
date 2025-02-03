import gradio as gr
import requests
import folium
from io import BytesIO
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de OpenWeatherMap
API_KEY_WEATHER = os.getenv("API_KEY_WEATHER") 
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Configuración de OpenCage Geocoder
API_KEY_GEOCODER = os.getenv("API_KEY_GEOCODER")
GEOCODER_URL = "https://api.opencagedata.com/geocode/v1/json"

# Configuración de OpenRouteService
API_KEY_ROUTE = os.getenv("API_KEY_ROUTE") 
ROUTE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def obtener_clima(ciudad):
    """Obtiene el clima actual para una ciudad usando OpenWeatherMap."""
    try:
        params = {
            "q": ciudad,
            "appid": API_KEY_WEATHER,
            "units": "metric",
            "lang": "es"
        }
        response = requests.get(WEATHER_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            clima = data['weather'][0]['description'].capitalize()
            temperatura = data['main']['temp']
            humedad = data['main']['humidity']
            viento = data['wind']['speed']
            return clima, temperatura, humedad, viento
        else:
            return "Error: No se pudo obtener el clima", None, None, None
    except Exception as e:
        return f"Error obteniendo el clima: {e}", None, None, None

def obtener_coordenadas(ciudad):
    """Obtiene las coordenadas de una ciudad usando OpenCage Geocoder."""
    try:
        params = {
            "q": ciudad,
            "key": API_KEY_GEOCODER,
            "limit": 1,
            "language": "es"
        }
        response = requests.get(GEOCODER_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                location = data["results"][0]["geometry"]
                return location["lat"], location["lng"]
            else:
                return None, None
        else:
            return None, None
    except Exception as e:
        print(f"Error obteniendo coordenadas: {e}")
        return None, None

def generar_mapa(origen, destino):
    """Genera un mapa interactivo con una ruta detallada entre dos ciudades."""
    try:
        lat_origen, lon_origen = obtener_coordenadas(origen)
        lat_destino, lon_destino = obtener_coordenadas(destino)

        if lat_origen is None or lat_destino is None:
            return "Error: No se encontraron coordenadas para una o ambas ciudades."

        # Llamada a la API de OpenRouteService para obtener la ruta
        headers = {"Authorization": API_KEY_ROUTE}
        params = {
            "start": f"{lon_origen},{lat_origen}",
            "end": f"{lon_destino},{lat_destino}"
        }
        response = requests.get(ROUTE_URL, headers=headers, params=params)

        if response.status_code != 200:
            return f"Error al obtener la ruta: {response.json().get('message', 'Desconocido')}"

        ruta = response.json()
        geometry = ruta["features"][0]["geometry"]["coordinates"]
        puntos = [(lat, lon) for lon, lat in geometry]

        # Crear el mapa con Folium
        mapa = folium.Map(location=[(lat_origen + lat_destino) / 2, (lon_origen + lon_destino) / 2], zoom_start=6)
        folium.Marker([lat_origen, lon_origen], popup=f"Origen: {origen}").add_to(mapa)
        folium.Marker([lat_destino, lon_destino], popup=f"Destino: {destino}").add_to(mapa)
        folium.PolyLine(puntos, color="blue", weight=2.5).add_to(mapa)

        # Convertir el mapa a HTML embebido
        mapa_html = BytesIO()
        mapa.save(mapa_html, close_file=False)
        mapa_html.seek(0)
        mapa_data = base64.b64encode(mapa_html.read()).decode('utf-8')

        return f'<iframe src="data:text/html;base64,{mapa_data}" width="100%" height="500px"></iframe>'
    except Exception as e:
        return f"Error generando el mapa: {e}"

# Diseño de la interfaz con Gradio
with gr.Blocks(css="""
    body {font-family: Arial, sans-serif; background-color: #1e293b; color: white;}
    .gr-button {background-color: #2563eb; color: white; border: none;}
    .gr-button:hover {background-color: #1d4ed8;}
""") as interfaz:
    gr.Markdown(
        """
        <div style="text-align: center;">
            <h1>BIKE-SENTRY</h1>
            <p>Obtén el clima actual y visualiza rutas detalladas entre ciudades</p>
        </div>
        """
    )

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Clima Actual")
            ciudad_input = gr.Textbox(label="Ciudad", placeholder="Ingresa el nombre de la ciudad")
            boton_clima = gr.Button("Consultar Clima")
            clima_output = gr.Textbox(label="Clima")
            temperatura_output = gr.Textbox(label="Temperatura")
            humedad_output = gr.Textbox(label="Humedad")
            viento_output = gr.Textbox(label="Viento")

            boton_clima.click(
                obtener_clima,
                inputs=ciudad_input,
                outputs=[clima_output, temperatura_output, humedad_output, viento_output]
            )

        with gr.Column():
            gr.Markdown("### Generar Ruta")
            origen_input = gr.Textbox(label="Ciudad de Origen", placeholder="Ingresa la ciudad de origen")
            destino_input = gr.Textbox(label="Ciudad de Destino", placeholder="Ingresa la ciudad de destino")
            boton_mapa = gr.Button("Generar Mapa")
            mapa_output = gr.HTML()

            boton_mapa.click(generar_mapa, inputs=[origen_input, destino_input], outputs=mapa_output)

if __name__ == "__main__":
    interfaz.launch()
