import os
import tempfile
from flask import Flask, request, jsonify, send_file, render_template
from threading import Thread
from moviepy.editor import VideoFileClip
import speech_recognition as sr

# Configuração do Flask
app = Flask(__name__)

# Pasta temporária para armazenar as partes do arquivo
UPLOAD_FOLDER = tempfile.mkdtemp()

# Rota principal para servir o frontend
@app.route('/')
def index():
    return render_template('index.html')

# Rota para receber partes do arquivo
@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    file = request.files['file']
    chunk_index = int(request.form['chunkIndex'])
    total_chunks = int(request.form['totalChunks'])
    file_name = request.form['fileName']

    # Salva a parte do arquivo em um arquivo temporário
    chunk_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.part{chunk_index}')
    file.save(chunk_path)

    return jsonify({"message": "Parte recebida com sucesso."})

# Função para processar o arquivo (extrair áudio e transcrever)
def process_file(file_name, total_chunks):
    try:
        # Reúne as partes do arquivo
        full_file_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.full')
        with open(full_file_path, 'wb') as full_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.part{i}')
                with open(chunk_path, 'rb') as chunk_file:
                    full_file.write(chunk_file.read())

        # Verifica se o arquivo é um vídeo
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            # Extrai o áudio do vídeo
            video = VideoFileClip(full_file_path)
            audio_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.wav')
            video.audio.write_audiofile(audio_path)
            video.close()
        else:
            # Se for um arquivo de áudio, usa diretamente
            audio_path = full_file_path

        # Transcreve o áudio
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data, language='pt-BR')

        # Salva a transcrição em um arquivo TXT
        transcript_path = os.path.join(UPLOAD_FOLDER, f'{file_name}_transcricao.txt')
        with open(transcript_path, 'w', encoding='utf-8') as transcript_file:
            transcript_file.write(transcript)

        # Limpa os arquivos temporários
        os.remove(full_file_path)
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            os.remove(audio_path)
        for i in range(total_chunks):
            os.remove(os.path.join(UPLOAD_FOLDER, f'{file_name}.part{i}'))

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")

# Rota para iniciar o processamento
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    file_name = data['fileName']
    total_chunks = data['totalChunks']

    # Inicia o processamento em uma thread separada
    thread = Thread(target=process_file, args=(file_name, total_chunks))
    thread.start()

    return jsonify({"message": "Processamento iniciado."})

# Rota para download da transcrição
@app.route('/download/<filename>')
def download(filename):
    transcript_path = os.path.join(UPLOAD_FOLDER, f'{filename}_transcricao.txt')
    return send_file(transcript_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)