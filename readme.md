# Conversor de transcritor de áudio ou vídeo

Este projeto é um conversor de arquivos de áudio MP4 para GIF, desenvolvido com Flask (Python) e implantado na Vercel. Ele permite que os usuários façam upload de arquivos MP4, convertam-nos para GIF e façam o download do arquivo convertido.


---

## Tecnologias Utilizadas

- **Flask**: Framework web em Python para criar a aplicação.
- **MoviePy**: Biblioteca para manipulação de vídeos e conversão para GIF.
- **Vercel**: Plataforma de implantação serverless.
- **HTML/CSS/JavaScript**: Frontend para interface do usuário.
- **Gunicorn**: Servidor WSGI para produção.

---

## Estrutura do Projeto

```
transcritor_audio_video/
│
├── api/                  # Pasta para funções serverless (opcional)
│   └── transcribe.js     # Exemplo de função serverless
├── app.py                # Código principal do Flask
├── build.sh              # Script de build (opcional)
├── readme.md             # Documentação do projeto
├── requirements.txt      # Dependências do projeto
├── static/               # Pasta para arquivos estáticos
│   ├── favicon.ico       # Ícone do site
│   ├── script.js         # Lógica do frontend
│   └── styles.css        # Estilos CSS
├── templates/            # Pasta para templates HTML
│   └── index.html        # Página principal
├── vercel.json           # Configuração do deploy na Vercel
└── wsgi.py               # Arquivo WSGI para produção
```

---

## Código do Projeto

### `app.py`
```python
from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import subprocess
import shutil
import speech_recognition as sr
from pydub import AudioSegment
import traceback
from threading import Thread

# Configuração do Flask
app = Flask(__name__)

# Pasta temporária para armazenar arquivos
UPLOAD_FOLDER = tempfile.mkdtemp()

# Rota principal para servir o frontend
@app.route('/')
def index():
    return render_template('index.html')

# Função para encontrar o FFmpeg
def find_ffmpeg():
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    common_locations = [
        r'C:\Program Files\FFmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\FFmpeg\ffmpeg.exe',
        r'C:\FFmpeg\bin\ffmpeg.exe',
        r'C:\Tools\FFmpeg\bin\ffmpeg.exe'
    ]
    for location in common_locations:
        if os.path.exists(location):
            return location
    raise FileNotFoundError("FFmpeg not found. Please install and add to PATH.")

# Função para extrair áudio de vídeo
def extract_audio(video_path, ffmpeg_path):
    try:
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        comando = [
            ffmpeg_path,
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]
        result = subprocess.run(comando, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Falha na extração de áudio: {result.stderr}")
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Erro ao extrair áudio: {e}")

# Função para transcrever áudio
def transcribe_audio(audio_path, language='pt-BR'):
    try:
        recognizer = sr.Recognizer()
        audio = AudioSegment.from_wav(audio_path)
        chunk_length = 30 * 1000  # 30 segundos
        chunks = [audio[i:i+chunk_length] for i in range(0, len(audio), chunk_length)]
        full_transcript = []
        for i, chunk in enumerate(chunks):
            chunk_path = f"temp_chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            try:
                with sr.AudioFile(chunk_path) as source:
                    audio_chunk = recognizer.record(source)
                    transcript = recognizer.recognize_google(audio_chunk, language=language)
                    full_transcript.append(transcript)
            except sr.UnknownValueError:
                print(f"Não foi possível transcrever o chunk {i+1}")
            except sr.RequestError as e:
                print(f"Erro na solicitação de transcrição: {e}")
            os.remove(chunk_path)
        return " ".join(full_transcript)
    except Exception as e:
        raise RuntimeError(f"Erro ao transcrever áudio: {e}")

# Função assíncrona para processar vídeo
def process_video_async(file_path, file_name):
    try:
        ffmpeg_path = find_ffmpeg()
        audio_path = extract_audio(file_path, ffmpeg_path)
        transcript = transcribe_audio(audio_path)
        txt_path = os.path.join(UPLOAD_FOLDER, f"{file_name}_transcricao.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        os.remove(audio_path)
    except Exception as e:
        print(f"Erro ao processar vídeo: {e}")

# Rota para upload de arquivos
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome do arquivo inválido."}), 400
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    thread = Thread(target=process_video_async, args=(file_path, os.path.splitext(file.filename)[0]))
    thread.start()
    return jsonify({"message": "Arquivo recebido e processamento iniciado."})

# Rota para download da transcrição
@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    txt_path = os.path.join(UPLOAD_FOLDER, f"{filename}_transcricao.txt")
    if not os.path.exists(txt_path):
        return jsonify({"error": "Arquivo não encontrado."}), 404
    return send_file(txt_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
```

---

### `templates/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcritor de Áudio/Video</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        <h1>Transcritor de Áudio/Video</h1>
        <form id="uploadForm">
            <input type="file" id="fileInput" accept=".mp4,.mkv,.avi,.mov,.wav,.mp3" required>
            <button type="submit">Enviar e Transcrever</button>
        </form>
        <p id="status"></p>
        <a id="downloadLink" style="display:none;">Baixar Transcrição</a>
    </div>
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
```

---

### `static/script.js`
```javascript
document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById('status').textContent = data.message;
            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = `/download/${file.name.split('.')[0]}`;
            downloadLink.style.display = 'block';
        } else if (data.error) {
            document.getElementById('status').textContent = data.error;
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });
});
```

---

### `static/styles.css`
```css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #f0f0f0;
}

.container {
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    text-align: center;
}

h1 {
    margin-bottom: 20px;
}

input[type="file"] {
    margin-bottom: 20px;
}

button {
    padding: 10px 20px;
    background-color: #007bff;
    color: #fff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

button:hover {
    background-color: #0056b3;
}

#downloadLink {
    margin-top: 20px;
    color: #007bff;
    text-decoration: none;
}
```

---

### `requirements.txt`
```txt
Flask==2.3.2
ffmpeg-python==0.2.0
gunicorn==20.1.0
pydub==0.25.1
SpeechRecognition==3.10.0
```

---

### `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "wsgi.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "wsgi.py"
    }
  ]
}
```

---

### `wsgi.py`
```python
from app import app

if __name__ == "__main__":
    app.run()
```

---

## Como Executar

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute o Flask:**
   ```bash
   python app.py
   ```

3. **Acesse no navegador:**
   Abra `http://localhost:5000` e faça upload de um arquivo de áudio ou vídeo.

4. **Implante na Vercel:**
   Use o comando `vercel --prod` para implantar o projeto.

---

## Funcionalidades

1. **Upload de Arquivos**: Aceita arquivos de áudio (WAV, MP3) e vídeo (MP4, MKV, AVI, etc.).
2. **Extração de Áudio**: Extrai áudio de vídeos usando FFmpeg.
3. **Transcrição**: Transcreve o áudio usando a API do Google Speech Recognition.
4. **Download da Transcrição**: Gera um arquivo `.txt` com a transcrição e disponibiliza para download.

---

## Observações

- Certifique-se de que o FFmpeg está instalado e acessível no sistema.
- O projeto pode ser adaptado para usar outras APIs de reconhecimento de fala, como Whisper da OpenAI.
- Para melhorar a precisão da transcrição, ajuste a taxa de amostragem e o idioma no código.


```

### 3. **Implantação na Vercel**

1. **Instale a CLI da Vercel:**
   ```bash
   npm install -g vercel
   ```

2. **Faça o Login na Vercel:**
   ```bash
   vercel login
   ```

3. **Faça o Deploy:**
   ```bash
   vercel --prod
   ```

---

### 4. **Testes**

- Acesse a URL fornecida pela Vercel.
- Faça upload de um arquivo MP4 e verifique se a conversão para GIF funciona corretamente.

---

## Licença

Este projeto está licenciado sob a MIT License. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.