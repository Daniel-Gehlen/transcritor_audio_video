document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const chunkSize = 5 * 1024 * 1024; // 5 MB por chunk
    const totalChunks = Math.ceil(file.size / chunkSize);

    for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append('file', chunk);
        formData.append('chunkIndex', i);
        formData.append('totalChunks', totalChunks);
        formData.append('fileName', file.name);

        try {
            const response = await fetch('/upload-chunk', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log(`Chunk ${i + 1}/${totalChunks} enviado:`, data);
        } catch (error) {
            console.error('Erro ao enviar chunk:', error);
            return;
        }
    }

    console.log('Todos os chunks foram enviados.');
    document.getElementById('status').textContent = 'Upload concluído!';
});