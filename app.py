import gradio as gr
import pyttsx3
import speech_recognition as sr
from transformers import pipeline

# Configuración de texto a voz
engine = pyttsx3.init()

# Configuración del modelo Whisper
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo")

# Función para capturar audio en tiempo real y procesarlo
def escuchar_y_procesar():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Esperando comandos...")
        try:
            # Ajustar el ruido ambiental
            recognizer.adjust_for_ambient_noise(source)
            # Capturar audio en tiempo real
            audio = recognizer.listen(source, timeout=10)
            # Convertir el audio en un archivo temporal para Whisper
            with open("temp_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())
            # Transcribir el audio usando Whisper
            result = pipe("temp_audio.wav")
            transcription = result["text"]
            print(f"Transcripción: {transcription}")

            if "SENTRY" in transcription.upper():
                respuesta = f"Asistente activado: procesando...'{transcription}'."
                engine.say(respuesta)
                engine.runAndWait()
                return respuesta
            else:
                return "Esperando la palabra clave 'SENTRY' para activarse."
        except Exception as e:
            return f"Error procesando el audio: {e}"

# Procesado de comandos por texto (para mantener compatibilidad con la interfaz)
def procesar_comando_por_voz(comando):
    if "SENTRY" in comando.upper():
        respuesta = f"Asistente activado: procesando...'{comando}'."
        engine.say(respuesta)
        engine.runAndWait()
        return respuesta
    else:
        return "Esperando la palabra clave 'SENTRY' para activarse."

# UI
with gr.Blocks(css=".gradio-container {background-color: black; color: white;}") as interfaz:
    gr.Markdown(
        """
        # 🏍️ **BIKESENTRY** 🏍️
        Usa la palabra **"SENTRY"** para activar el asistente.
        """,
        elem_id="titulo"
    )

    # Fila 1: Clima y Música
    with gr.Row(equal_height=True):
        # Clima
        with gr.Column(scale=1):
            gr.Markdown("### 🌤️ Clima y Tiempo 🌤️", elem_id="clima_titulo")
            gr.Label("Clima actual: 22°C, Soleado", elem_id="clima_info")

        # Música
        with gr.Column(scale=1):
            gr.Markdown("### 🎵 Música 🎵", elem_id="musica_titulo")
            gr.Audio(label="Control de música")

    # Fila 2: Mapa
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🗺️ Mapa y Rutas 🗺️", elem_id="mapa_titulo")
            gr.Image("mapa.avif", label="Mapa", elem_id="mapa")

    # Fila 3: Asistente
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎙️ Control por Voz", elem_id="voz_titulo")
            entrada_voz = gr.Textbox(
                placeholder="Comando",
                label="Entrada ",
                elem_id="entrada_voz",
                lines=2,
                interactive=True,
                show_label=False
            )
            salida_respuesta = gr.Textbox(
                label="Respuesta",
                elem_id="salida_respuesta",
                lines=3,
                interactive=False,
                show_label=False
            )

    # Conexión E/S
    entrada_voz.change(procesar_comando_por_voz, inputs=entrada_voz, outputs=salida_respuesta)

# Reconocimiento continuo en segundo plano
import threading

def reconocimiento_continuo():
    while True:
        respuesta = escuchar_y_procesar()
        print(respuesta)

# Ejecutar reconocimiento en un hilo separado
reconocimiento_hilo = threading.Thread(target=reconocimiento_continuo, daemon=True)
reconocimiento_hilo.start()

# Init
if __name__ == "__main__":
    interfaz.launch()
