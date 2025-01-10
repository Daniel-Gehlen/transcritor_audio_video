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

        // Configura o SSE para receber o progresso
        const eventSource = new EventSource('/progress');
        eventSource.onmessage = function (event) {
            const data = JSON.parse(event.data);

            if (data.progress) {
                // Atualiza a barra de progresso
                const progressBar = document.getElementById('progressBar');
                progressBar.style.width = `${data.progress}%`;
                progressBar.textContent = `${data.progress}%`;
            }

            if (data.file) {
                // Finaliza o progresso e faz o download do arquivo
                const link = document.createElement('a');
                link.href = data.file; // URL do arquivo gerado pelo backend
                link.download = 'transcricao.txt'; // Nome do arquivo para download
                link.click();
                document.getElementById('status').textContent = 'Transcrição concluída!';
                eventSource.close();
            }

            if (data.error) {
                // Exibe mensagem de erro
                document.getElementById('status').textContent = data.error;
                eventSource.close();
            }
        };
    } catch (error) {
        console.error('Erro ao iniciar processamento:', error);
        document.getElementById('status').textContent = 'Erro ao processar arquivo.';
    }
});