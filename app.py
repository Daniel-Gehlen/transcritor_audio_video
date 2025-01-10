from flask import Flask, render_template, request, jsonify, send_file
import io
import subprocess
import shutil
import speech_recognition as sr
from moviepy.editor import VideoFileClip
from threading import Thread

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
def extract_audio(video_bytes, ffmpeg_path):
    try:
        # Cria um arquivo temporário em memória
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
            temp_video.write(video_bytes)
            temp_video_path = temp_video.name

        # Extrai o áudio em memória
        audio_path = temp_video_path.replace(".mp4", ".wav")
        comando = [
            ffmpeg_path,
            "-i", temp_video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]
        subprocess.run(comando, capture_output=True, text=True, check=True)

        # Lê o áudio extraído
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        # Remove os arquivos temporários
        os.remove(temp_video_path)
        os.remove(audio_path)

        return audio_bytes
    except Exception as e:
        raise RuntimeError(f"Erro ao extrair áudio: {e}")

# Função para transcrever áudio
def transcribe_audio(audio_bytes, language='pt-BR'):
    try:
        recognizer = sr.Recognizer()
        audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
        chunk_length = 30 * 1000  # 30 segundos
        chunks = [audio[i:i+chunk_length] for i in range(0, len(audio), chunk_length)]
        full_transcript = []

        for i, chunk in enumerate(chunks):
            chunk_bytes = io.BytesIO()
            chunk.export(chunk_bytes, format="wav")
            chunk_bytes.seek(0)
            try:
                with sr.AudioFile(chunk_bytes) as source:
                    audio_chunk = recognizer.record(source)
                    transcript = recognizer.recognize_google(audio_chunk, language=language)
                    full_transcript.append(transcript)
            except sr.UnknownValueError:
                print(f"Não foi possível transcrever o chunk {i+1}")
            except sr.RequestError as e:
                print(f"Erro na solicitação de transcrição: {e}")

        return " ".join(full_transcript)
    except Exception as e:
        raise RuntimeError(f"Erro ao transcrever áudio: {e}")

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
            download_name=f"{file.filename.split('.')[0]}_transcricao.txt",
            mimetype="text/plain"
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao processar o arquivo: {e}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)