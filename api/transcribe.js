document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Configura o SSE para receber o progresso
    const eventSource = new EventSource('/upload');
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
            link.href = `data:audio/mpeg;base64,${data.file}`;
            link.download = 'converted.mp3';
            link.click();
            document.getElementById('status').textContent = 'Conversão concluída!';
            eventSource.close();
        }

        if (data.error) {
            // Exibe mensagem de erro
            document.getElementById('status').textContent = data.error;
            eventSource.close();
        }
    };

    // Envia o arquivo para o backend
    fetch('/upload', {
        method: 'POST',
        body: formData
    });
});