from flask import Flask, request, jsonify, send_file, render_template
import io
import subprocess
import speech_recognition as sr
import shutil
import os

# Configuração do Flask
app = Flask(__name__)

# Rota principal para servir o frontend
@app.route('/')
def index():
    return render_template('index.html')

# Função para encontrar o FFmpeg
def find_ffmpeg():
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    raise FileNotFoundError("FFmpeg não encontrado. Por favor, instale o FFmpeg e adicione ao PATH.")

# Função para extrair áudio de vídeo (em memória)
def extract_audio(video_bytes, ffmpeg_path):
    try:
        # Executa o FFmpeg diretamente no buffer de entrada
        comando = [
            ffmpeg_path,
            "-i", "pipe:0",  # Entrada via pipe (buffer de memória)
            "-vn",           # Ignora o vídeo
            "-acodec", "pcm_s16le",  # Codec de áudio PCM WAV
            "-ar", "16000",  # Taxa de amostragem (16 kHz)
            "-ac", "1",      # Canal mono
            "-f", "wav",     # Formato de saída WAV
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

# Função para converter áudio para WAV PCM (em memória)
def convert_audio_to_wav(audio_bytes, ffmpeg_path):
    try:
        # Executa o FFmpeg para converter o áudio para WAV PCM
        comando = [
            ffmpeg_path,
            "-i", "pipe:0",  # Entrada via pipe (buffer de memória)
            "-acodec", "pcm_s16le",  # Codec de áudio PCM WAV
            "-ar", "16000",  # Taxa de amostragem (16 kHz)
            "-ac", "1",      # Canal mono
            "-f", "wav",     # Formato de saída WAV
            "pipe:1"         # Saída via pipe (buffer de memória)
        ]
        process = subprocess.run(
            comando,
            input=audio_bytes,
            capture_output=True,
            check=True
        )
        return process.stdout  # Retorna o áudio convertido como bytes
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erro ao converter áudio: {e.stderr.decode()}")

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

# Rota para upload e processamento
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome do arquivo inválido."}), 400

    try:
        file_bytes = file.read()

        # Verifica se é um vídeo e extrai o áudio
        if file.filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            ffmpeg_path = find_ffmpeg()
            audio_bytes = extract_audio(file_bytes, ffmpeg_path)
        else:
            # Se for um arquivo de áudio, converte para WAV PCM
            ffmpeg_path = find_ffmpeg()
            audio_bytes = convert_audio_to_wav(file_bytes, ffmpeg_path)

        # Transcreve o áudio
        transcript = transcribe_audio(audio_bytes)

        # Cria um arquivo TXT em memória
        txt_file = io.BytesIO(transcript.encode('utf-8'))
        txt_file.seek(0)

        # Retorna o arquivo TXT para download
        return send_file(
            txt_file,
            as_attachment=True,
            download_name=f"{file.filename.split('.')[0]}_transcricao.txt",
            mimetype="text/plain"
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao processar o arquivo: {str(e)}"}), 500

# Rota para lidar com métodos não permitidos
@app.route('/upload', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def upload_method_not_allowed():
    return jsonify({"error": "Método não permitido. Use POST."}), 405

# Rota para servir o favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)