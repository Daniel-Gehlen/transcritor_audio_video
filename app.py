from flask import Flask, request, jsonify, send_file, render_template
import os
import io
import subprocess
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import shutil

# Configuração do Flask
app = Flask(__name__)

# Pasta temporária para armazenar chunks (usando /tmp)
UPLOAD_FOLDER = '/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    raise FileNotFoundError("FFmpeg não encontrado. Por favor, instale o FFmpeg e adicione ao PATH.")

# Função para extrair áudio de vídeo (em memória)
def extract_audio(video_bytes, ffmpeg_path):
    try:
        # Executa o FFmpeg diretamente no buffer de entrada
        comando = [
            ffmpeg_path,
            "-i", "pipe:0",  # Entrada via pipe (buffer de memória)
            "-vn",           # Ignora o vídeo
            "-acodec", "pcm_s16le",  # Codec de áudio
            "-ar", "16000",  # Taxa de amostragem
            "-ac", "1",      # Canal mono
            "-f", "wav",     # Formato de saída
            "pipe:1"         # Saída via pipe (buffer de memória)
        ]
        process = subprocess.run(
            comando,
            input=video_bytes,
            capture_output=True,
            check=True
        )
        return process.stdout  # Retorna o áudio extraído como bytes
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erro ao extrair áudio: {e.stderr.decode()}")

# Função para transcrever áudio (em memória)
def transcribe_audio(audio_bytes, language='pt-BR'):
    try:
        recognizer = sr.Recognizer()
        audio = sr.AudioFile(io.BytesIO(audio_bytes))
        with audio as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data, language=language)
        return transcript
    except sr.UnknownValueError:
        raise RuntimeError("Não foi possível transcrever o áudio.")
    except sr.RequestError as e:
        raise RuntimeError(f"Erro na solicitação de transcrição: {e}")

# Rota para receber chunks
@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    file = request.files['file']
    chunk_index = int(request.form['chunkIndex'])
    total_chunks = int(request.form['totalChunks'])
    file_name = request.form['fileName']

    # Salva o chunk em um arquivo temporário
    chunk_path = os.path.join(UPLOAD_FOLDER, f"{file_name}.part{chunk_index}")
    file.save(chunk_path)

    if chunk_index == total_chunks - 1:
        # Combina os chunks em um único arquivo
        full_file_path = os.path.join(UPLOAD_FOLDER, file_name)
        with open(full_file_path, 'wb') as full_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(UPLOAD_FOLDER, f"{file_name}.part{i}")
                with open(chunk_path, 'rb') as chunk_file:
                    full_file.write(chunk_file.read())
                os.remove(chunk_path)  # Remove o chunk após a combinação

        # Processa o arquivo completo
        try:
            with open(full_file_path, 'rb') as f:
                file_bytes = f.read()

            # Verifica se é um vídeo e extrai o áudio
            if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                ffmpeg_path = find_ffmpeg()
                audio_bytes = extract_audio(file_bytes, ffmpeg_path)
            else:
                audio_bytes = file_bytes

            # Transcreve o áudio
            transcript = transcribe_audio(audio_bytes)

            # Cria um arquivo TXT em memória
            txt_file = io.BytesIO(transcript.encode('utf-8'))
            txt_file.seek(0)

            # Retorna o arquivo TXT para download
            return send_file(
                txt_file,
                as_attachment=True,
                download_name=f"{file_name.split('.')[0]}_transcricao.txt",
                mimetype="text/plain"
            )

        except Exception as e:
            return jsonify({"error": f"Erro ao processar o arquivo: {e}"}), 500

    return jsonify({"message": "Chunk recebido com sucesso."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)