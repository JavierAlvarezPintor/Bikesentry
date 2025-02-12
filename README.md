# 🏍️ BIKE-SENTRY 🔒  
🚀 Aplicación para **motoristas** que proporciona información meteorológica, generación de rutas seguras y comandos de voz con transcripción y respuesta de IA.

---

## 📌 Características
✔ **🌦️ Clima en tu ruta** – Obtén información del clima antes de viajar.  
✔ **🛠️ Generación de rutas seguras** – Usa OpenRouteService para planificar tu viaje.  
✔ **🎤 Comandos de voz** – Graba tu voz y obtén una salida en texto y audio.  
✔ **🤖 IA integrada** – Usa modelos de Llama y Whisper para mejorar la interacción (Dependiendo de tu memoria VRAM).  

---

## 🛠️ Instalación

### **1️⃣ Clona el repositorio**
```bash
git clone https://github.com/JavierAlvarezPintor/bike-sentry.git
cd bike-sentry
```

### **2️⃣ Crea un entorno virtual (opcional, pero recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/macOS
```

### **3️⃣ Instala las dependencias**
```bash
pip install -r requirements.txt
```

> 📌 **Nota:** Si tienes problemas con `pyaudio`, instálalo manualmente:  
> - **Linux**: `sudo apt install portaudio19-dev && pip install pyaudio`   
> - **MacOS**: `brew install portaudio && pip install pyaudio`  

---

## 🔑 Configuración
Crea un archivo **`.env`** en el directorio raíz y agrega tus claves de API:

```ini
API_KEY_WEATHER=tu_clave_openweathermap
API_KEY_GEOCODER=tu_clave_opencage
API_KEY_ROUTE=tu_clave_openrouteservice
```

> 📌 **Nota:** Puedes obtener las claves en:  
> - [OpenWeatherMap](https://home.openweathermap.org/api_keys)  
> - [OpenCage Geocoder](https://opencagedata.com/api)  
> - [OpenRouteService](https://openrouteservice.org/sign-up/)  

---

## 🚀 Ejecución
Para iniciar la aplicación, ejecuta:
```bash
python3 bikeSentry.py
```

Una vez iniciada, Gradio abrirá una interfaz web en tu navegador.

---

## 📆 Dependencias Principales
- `gradio` – Interfaz gráfica interactiva  
- `requests` – Consultas HTTP a APIs externas  
- `folium` – Generación de mapas interactivos  
- `dotenv` – Carga de variables de entorno  
- `whisper` – Transcripción de voz a texto  
- `pyaudio` – Captura de audio en tiempo real  
- `torch` – Librería base para modelos de IA  
- `llama_cpp` – Implementación de modelos de lenguaje Llama  

---

## ❓ Problemas Comunes y Soluciones

### **🔹 Error: `torch.cuda.is_available() == False`**
📌 **Solución:** Si tienes una GPU compatible, instala PyTorch con CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### **🔹 Error: `pyaudio` no se instala**
📌 **Solución:** Instala manualmente según tu sistema operativo (ver sección de instalación).  


---

## 🛠️ Mejoras Futuras
- 🔄 **Integración con bases de datos para guardar rutas favoritas**  
- 🎧 **Mejora en la calidad del procesamiento de entrada**  
- ⛔ **Alertas de tráfico y accidentes en tiempo real**  

---

## 🤝 Contribuciones
📌 **Toda ayuda es bienvenida**. Si quieres contribuir:  
1. Haz un **fork** del repositorio  
2. Crea una **rama nueva** (`git checkout -b nueva-feature`)  
3. Realiza tus cambios y sube un **pull request**  

---

## 📚 Licencia
Este proyecto está bajo la licencia **MIT**. Puedes usarlo y modificarlo libremente.

---

🚀 **BIKE-SENTRY: Viaja seguro, navega con inteligencia.** 🏍️🛠️🔒

