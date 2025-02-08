import gradio as gr
import requests
import folium
from io import BytesIO
import base64
from dotenv import load_dotenv
import os
import whisper
import pyaudio
import wave
import numpy as np
import subprocess
import torch
import threading
from llama_cpp import Llama

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

# Configuración de grabación
CHUNK = 1024  # Tamaño de cada fragmento de audio
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100  # Frecuencia de muestreo
RECORD_SECONDS = 5  # Duración de la grabación

# Inicializar modelo Whisper
model = whisper.load_model("turbo", device="cuda" if torch.cuda.is_available() else "cpu")

# Inicializar modelo Llama
llm = Llama.from_pretrained(
    repo_id="Qwen/Qwen2-0.5B-Instruct-GGUF",
    filename="*q8_0.gguf",
    verbose=False
)

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

# Crear un mapa base vacío al inicio
def mapa_inicial():
    mapa = folium.Map(location=[40.4168, -3.7038], zoom_start=6)  # Madrid como ejemplo
    mapa_html = BytesIO()
    mapa.save(mapa_html, close_file=False)
    mapa_html.seek(0)
    mapa_data = base64.b64encode(mapa_html.read()).decode('utf-8')
    return f'<iframe src="data:text/html;base64,{mapa_data}" width="100%" height="500px"></iframe>'

def generar_mapa(origen, destino):
    try:
        lat_origen, lon_origen = obtener_coordenadas(origen)
        lat_destino, lon_destino = obtener_coordenadas(destino)

        if lat_origen is None or lat_destino is None:
            return "Error: No se encontraron coordenadas."

        headers = {"Authorization": API_KEY_ROUTE}
        params = {"start": f"{lon_origen},{lat_origen}", "end": f"{lon_destino},{lat_destino}"}
        response = requests.get(ROUTE_URL, headers=headers, params=params)

        if response.status_code != 200:
            return f"Error al obtener la ruta: {response.json().get('message', 'Desconocido')}"

        ruta = response.json()
        geometry = ruta["features"][0]["geometry"]["coordinates"]
        puntos = [(lat, lon) for lon, lat in geometry]

        # Crear el mapa y ajustar el zoom automáticamente
        mapa = folium.Map()
        folium.Marker([lat_origen, lon_origen], popup=f"Origen: {origen}").add_to(mapa)
        folium.Marker([lat_destino, lon_destino], popup=f"Destino: {destino}").add_to(mapa)
        folium.PolyLine(puntos, color="blue", weight=2.5).add_to(mapa)

        # Ajustar zoom al recorrido
        sw = [min(p[0] for p in puntos), min(p[1] for p in puntos)]
        ne = [max(p[0] for p in puntos), max(p[1] for p in puntos)]
        mapa.fit_bounds([sw, ne])

        # Convertir el mapa a HTML
        mapa_html = BytesIO()
        mapa.save(mapa_html, close_file=False)
        mapa_html.seek(0)
        mapa_data = base64.b64encode(mapa_html.read()).decode('utf-8')

        return f'<iframe src="data:text/html;base64,{mapa_data}" width="100%" height="500px"></iframe>'
    except Exception as e:
        return f"Error generando el mapa: {e}"
  
def reproducir_audio(tts_output):
    subprocess.run(["aplay", tts_output])

def grabar_y_transcribir():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

    print("Escuchando...")
    frames = []

    # Grabación de audio
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(np.frombuffer(data, dtype=np.int16))

    print("Procesando...")

    # Detener la grabación
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Guardar audio temporalmente
    filename = "temp_audio.wav"
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join([frame.tobytes() for frame in frames]))
    wf.close()

    # Transcribir audio
    result = model.transcribe(filename, language='es' if 'es' in whisper.tokenizer.LANGUAGES else 'en')
    transcribed_text = result["text"]
    
    # Pasar la transcripción a Llama como pregunta
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "Eres un asistente útil."},
            {"role": "user", "content": transcribed_text}
        ]
    )
    
    respuesta_llama = response['choices'][0]['message']['content']
    
    # Mostrar el texto de la respuesta antes de generar el audio
    print("Respuesta de Llama:", respuesta_llama)
    
    # Convertir texto a voz usando Piper en segundo plano
    tts_output = "output_audio.wav"
    subprocess.run(["bash", "-c",
        f'echo "{respuesta_llama}" | piper --model /home/javi/piper_models/es_ES-davefx-medium.onnx '
        f'--config /home/javi/piper_models/es_ES-davefx-medium.onnx.json '
        f'--output_file {tts_output} '
        f'--espeak_data /usr/lib/x86_64-linux-gnu/espeak-ng-data/'
    ])
    
    # Iniciar la reproducción del audio en un hilo separado
    threading.Thread(target=reproducir_audio, args=(tts_output,)).start()
    
    return transcribed_text, respuesta_llama


# Diseño de la interfaz con Gradio
with gr.Blocks(css="""
    body {font-family: Arial, sans-serif; background-color: #1e293b; color: white;}
    .gr-button {background-color: #2563eb; color: white; border: none;}
    .gr-button:hover {background-color: #1d4ed8;}
""") as interfaz:
    gr.Markdown("<h1 style='text-align: center;'>🏍️ BIKE-SENTRY 🔒</h1><p style='text-align: center;'>🛡️ Tu asistente para seguridad y rutas en moto 🛣️</p>")


    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🌦️ Consulta el Clima en tu Ruta")
            ciudad_input = gr.Textbox(label="📍 Ciudad", placeholder="Ingresa el nombre de la ciudad")
            boton_clima = gr.Button("🔍 Consultar Clima")
            clima_output = gr.Textbox(label="☁️ Estado del Clima")
            temperatura_output = gr.Textbox(label="🌡️ Temperatura (°C)")
            humedad_output = gr.Textbox(label="💧 Humedad (%)")
            viento_output = gr.Textbox(label="🌬️ Velocidad del Viento (km/h)")

            boton_clima.click(obtener_clima, inputs=ciudad_input, outputs=[clima_output, temperatura_output, humedad_output, viento_output])

            gr.Markdown("### 🎤 Asistente de conducción")
            boton_grabar = gr.Button("🎙️ Activar")
            transcripcion_output = gr.Textbox(label="📝 Transcripción")
            respuesta_output = gr.Textbox(label="🤖 Respuesta")

            boton_grabar.click(grabar_y_transcribir, inputs=[], outputs=[transcripcion_output, respuesta_output])

        with gr.Column():
            gr.Markdown("### 🗺️ Planifica tu Ruta ")
            origen_input = gr.Textbox(label="🏁 Ciudad de Origen", placeholder="Ej: Madrid")
            destino_input = gr.Textbox(label="🎯 Ciudad de Destino", placeholder="Ej: Barcelona")
            boton_mapa = gr.Button("🛣️ Generar Ruta Segura")
            
            # Mapa cargado por defecto sin ruta
            mapa_output = gr.HTML(value=mapa_inicial())

            boton_mapa.click(generar_mapa, inputs=[origen_input, destino_input], outputs=mapa_output)

if __name__ == "__main__":
    interfaz.launch()
