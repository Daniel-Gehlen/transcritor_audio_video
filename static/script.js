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

            if (!response.ok) {
                throw new Error('Erro ao enviar chunk.');
            }

            const data = await response.json();
            console.log(`Chunk ${i + 1}/${totalChunks} enviado:`, data);
        } catch (error) {
            console.error('Erro ao enviar chunk:', error);
            document.getElementById('status').textContent = 'Erro ao enviar arquivo.';
            return;
        }
    }

    console.log('Todos os chunks foram enviados.');
    document.getElementById('status').textContent = 'Upload concluído! Iniciando processamento...';

    // Inicia o processamento
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fileName: file.name,
                totalChunks: totalChunks
            })
        });

        if (!response.ok) {
            throw new Error('Erro ao iniciar processamento.');
        }

        const data = await response.json();
        console.log('Processamento iniciado:', data);

        // Aguarda o processamento e faz o download da transcrição
        setTimeout(() => {
            window.location.href = `/download/${file.name}`;
        }, 5000); // Aguarda 5 segundos (ajuste conforme necessário)
    } catch (error) {
        console.error('Erro ao iniciar processamento:', error);
        document.getElementById('status').textContent = 'Erro ao processar arquivo.';
    }
});