import gradio as gr
import requests
import folium
from io import BytesIO
import base64  # Para codificar el archivo del mapa en base64
import tempfile

# Configuración de OpenWeatherMap
API_KEY_WEATHER = "174cfbb31ba5b64b295b53a9f81247e7"  # clave API
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Configuración de OpenRouteService
API_KEY_ROUTE = "5b3ce3597851110001cf62481ccfcee649ea4d148895fe0368df7f73"  # clave API
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
    """Obtiene las coordenadas de una ciudad usando OpenWeatherMap."""
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
            lat = data['coord']['lat']
            lon = data['coord']['lon']
            return lat, lon
        else:
            return None, None
    except Exception as e:
        return None, None

import tempfile
import base64
import folium
import os

def generar_ruta(ciudad_origen, ciudad_destino):
    """Genera una ruta entre dos ciudades usando OpenRouteService."""
    try:
        lat_origen, lon_origen = obtener_coordenadas(ciudad_origen)
        lat_destino, lon_destino = obtener_coordenadas(ciudad_destino)
        
        if lat_origen is None or lat_destino is None:
            return "Error: No se pudieron obtener las coordenadas de una de las ciudades."
        
        headers = {
            'Authorization': API_KEY_ROUTE
        }
        body = {
            "coordinates": [[lon_origen, lat_origen], [lon_destino, lat_destino]],
            "instructions": "false"
        }

        response = requests.post(ROUTE_URL, json=body, headers=headers)
        
        if response.status_code != 200:
            return f"Error: statuscode {response.status_code}. Respuesta: {response.text}"

        data = response.json()

        # Verificar si 'features' está presente en la respuesta
        if 'features' not in data or not data['features']:
            return f"Error: La respuesta no contiene una ruta válida. Respuesta: {response.text}"
        
        ruta = data['features'][0]['geometry']['coordinates']

        # Crear el mapa
        mapa = folium.Map(location=[lat_origen, lon_origen], zoom_start=12)
        folium.Marker([lat_origen, lon_origen], popup=f"Origen: {ciudad_origen}").add_to(mapa)
        folium.Marker([lat_destino, lon_destino], popup=f"Destino: {ciudad_destino}").add_to(mapa)
        folium.PolyLine(locations=[(lat, lon) for lon, lat in ruta], color="blue", weight=5, opacity=0.7).add_to(mapa)

        # Crear un archivo temporal para guardar el mapa
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            mapa.save(tmp_file.name)
            tmp_file_path = tmp_file.name

        # Leer el archivo HTML y codificarlo en base64
        with open(tmp_file_path, "rb") as file:
            map_data = base64.b64encode(file.read()).decode('utf-8')

        # Eliminar el archivo temporal
        os.remove(tmp_file_path)
        
        # Crear un enlace HTML para mostrar el mapa
        return f'<iframe src="data:text/html;base64,{map_data}" width="100%" height="500px"></iframe>'
    except Exception as e:
        return f"Error obteniendo la ruta: {e}"


# Diseño Interfaz Gradio
with gr.Blocks() as interfaz:
    gr.Markdown(
        """
        # 🌦️ **BIKESENTRY** 🚗
        ### 🚀 Consulta el clima y planifica tu ruta.
        """
    )
    
    # Sección Clima
    with gr.Row():
        ciudad_input = gr.Textbox(label="Ciudad", placeholder="Ingresa el nombre de la ciudad", elem_id="ciudad-input", lines=1)
        boton_clima = gr.Button("Consultar Clima", elem_id="boton-clima", size="lg")
    
    with gr.Row():
        clima_output = gr.Textbox(label="Clima", interactive=False, elem_id="clima-output", lines=1, max_lines=1, show_label=False)
        temperatura_output = gr.Textbox(label="Temperatura", interactive=False, elem_id="temperatura-output", lines=1, max_lines=1, show_label=False)
    with gr.Row():
        humedad_output = gr.Textbox(label="Humedad", interactive=False, elem_id="humedad-output", lines=1, max_lines=1, show_label=False)
        viento_output = gr.Textbox(label="Viento", interactive=False, elem_id="viento-output", lines=1, max_lines=1, show_label=False)

    boton_clima.click(obtener_clima, inputs=ciudad_input, outputs=[clima_output, temperatura_output, humedad_output, viento_output])

    # Mapa Interactivo y Ruta
    with gr.Row():
        gr.Markdown("## 🗺️ **Ruta entre dos ciudades**")
        ciudad_origen_input = gr.Textbox(label="Ciudad de Origen", placeholder="Ingresa el nombre de la ciudad de origen", elem_id="ciudad-origen-input", lines=1)
        ciudad_destino_input = gr.Textbox(label="Ciudad de Destino", placeholder="Ingresa el nombre de la ciudad de destino", elem_id="ciudad-destino-input", lines=1)
        boton_ruta = gr.Button("Ver Ruta", elem_id="boton-ruta", size="lg")
    
    with gr.Row():
        mapa_output = gr.HTML(label="Mapa de la Ruta")

    boton_ruta.click(generar_ruta, inputs=[ciudad_origen_input, ciudad_destino_input], outputs=mapa_output)

# Estilos
interfaz.css = """
#ciudad-input, #boton-clima, #boton-ruta {
    font-size: 20px;
}

#clima-output, #temperatura-output, #humedad-output, #viento-output {
    font-size: 24px;
    font-weight: bold;
    background-color: #f0f8ff;
    padding: 20px;
    margin: 10px;
    border-radius: 10px;
    text-align: center;
    color: #333;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}

#boton-clima, #boton-ruta {
    background-color: #4caf50;
    color: white;
    padding: 15px;
    font-size: 18px;
    border-radius: 10px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}

#boton-clima:hover, #boton-ruta:hover {
    background-color: #45a049;
    cursor: pointer;
}
"""

# Main
if __name__ == "__main__":
    interfaz.launch()
