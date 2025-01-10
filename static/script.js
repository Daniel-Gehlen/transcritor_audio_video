document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const chunkSize = 1 * 1024 * 1024; // 1 MB por chunk
    const totalChunks = Math.ceil(file.size / chunkSize);

    let combinedBytes = new Uint8Array(file.size); // Array para combinar os chunks
    let bytesReceived = 0;

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
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Erro ao enviar chunk.');
            }

            const data = await response.arrayBuffer();
            combinedBytes.set(new Uint8Array(data), start); // Combina os chunks
            bytesReceived += data.byteLength;

            console.log(`Chunk ${i + 1}/${totalChunks} enviado e processado.`);
        } catch (error) {
            console.error('Erro ao enviar chunk:', error);
            return;
        }
    }

    console.log('Todos os chunks foram enviados e processados.');
    document.getElementById('status').textContent = 'Transcrição concluída!';

    // Cria um link para download do arquivo transcrito
    const blob = new Blob([combinedBytes], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${file.name.split('.')[0]}_transcricao.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
});