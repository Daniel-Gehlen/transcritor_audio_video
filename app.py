from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import subprocess
import shutil
import speech_recognition as sr
from moviepy.editor import VideoFileClip
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
    raise FileNotFoundError("FFmpeg não encontrado. Por favor, instale o FFmpeg e adicione ao PATH.")

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

# Função assíncrona para processar o arquivo
def process_file_async(file_path, file_name):
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Se for um vídeo, extrai o áudio
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            audio_path = extract_audio(file_path, ffmpeg_path)
        else:
            audio_path = file_path

        # Transcreve o áudio
        transcript = transcribe_audio(audio_path)

        # Salva a transcrição em um arquivo de texto
        txt_path = os.path.join(UPLOAD_FOLDER, f"{os.path.splitext(file_name)[0]}_transcricao.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        # Remove o arquivo de áudio temporário (se criado)
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            os.remove(audio_path)

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")

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
    thread = Thread(target=process_file_async, args=(file_path, file.filename))
    thread.start()
    return jsonify({"message": "Arquivo recebido e processamento iniciado."})

# Rota para download da transcrição
@app.route('/download/<filename>')
def download(filename):
    txt_path = os.path.join(UPLOAD_FOLDER, f"{filename}_transcricao.txt")
    if not os.path.exists(txt_path):
        return jsonify({"error": "Arquivo não encontrado."}), 404
    return send_file(txt_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)