import os
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    file = request.files['file']
    chunk_index = int(request.form['chunkIndex'])
    total_chunks = int(request.form['totalChunks'])
    file_name = request.form['fileName']

    chunk_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.part{chunk_index}')
    file.save(chunk_path)

    if chunk_index == total_chunks - 1:
        # Combina os chunks
        full_file_path = os.path.join(UPLOAD_FOLDER, file_name)
        with open(full_file_path, 'wb') as full_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(UPLOAD_FOLDER, f'{file_name}.part{i}')
                with open(chunk_path, 'rb') as chunk_file:
                    full_file.write(chunk_file.read())
                os.remove(chunk_path)  

        return jsonify({"message": "Upload e combinação concluídos."})

    return jsonify({"message": "Chunk recebido com sucesso."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)