from flask import Flask, request, jsonify, Response, send_file
import os
import tempfile
from threading import Thread
from moviepy.editor import VideoFileClip
import speech_recognition as sr

# Configuração do Flask
app = Flask(__name__)

# Aumenta o limite de tamanho de payload para 50 MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# Pasta temporária para armazenar arquivos
UPLOAD_FOLDER = tempfile.mkdtemp()

# Rota para receber partes do arquivo (chunks)
@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    file = request.files['file']
    chunk_index = int(request.form['chunkIndex'])
    total_chunks = int(request.form['totalChunks'])
    file_name = request.form['fileName']

    # Salva a parte do arquivo em um arquivo temporário
    chunk_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.part{chunk_index}')
    file.save(chunk_path)

    return jsonify({"message": "Parte recebida com sucesso."})

# Rota para iniciar o processamento
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    file_name = data['fileName']
    total_chunks = data['totalChunks']

    # Inicia o processamento em uma thread separada
    Thread(target=process_file, args=(file_name, total_chunks)).start()

    return jsonify({"message": "Processamento iniciado."})

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

        # Envia o progresso via SSE
        def send_progress(progress):
            return f"data: {json.dumps({'progress': progress})}\n\n"

        def send_file_url(url):
            return f"data: {json.dumps({'file': url})}\n\n"

        # Simula o progresso (substitua por um progresso real)
        for i in range(0, 101, 10):
            Response(send_progress(i), content_type='text/event-stream')

        # Retorna a URL do arquivo para download
        Response(send_file_url(f'/download/{file_name}_transcricao.txt'), content_type='text/event-stream')

    except Exception as e:
        Response(f"data: {json.dumps({'error': str(e)})}\n\n", content_type='text/event-stream')

# Rota para download da transcrição
@app.route('/download/<filename>')
def download(filename):
    transcript_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(transcript_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)