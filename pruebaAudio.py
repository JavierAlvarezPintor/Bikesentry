import whisper
import pyaudio
import wave
import numpy as np
import gradio as gr
import subprocess
import torch
import threading
from llama_cpp import Llama

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

iface = gr.Interface(fn=grabar_y_transcribir, inputs=[], outputs=["text", "text"], title="Transcripción con Whisper y Llama", description="Presiona el botón para grabar y obtener respuesta de Llama.")
iface.launch()
