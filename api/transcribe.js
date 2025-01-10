document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Por favor, selecione um arquivo.');
        return;
    }

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

    // Envia o arquivo para o backend
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao enviar arquivo.');
        }
    })
    .catch(error => {
        console.error('Erro ao enviar arquivo:', error);
        document.getElementById('status').textContent = 'Erro ao enviar arquivo.';
        eventSource.close();
    });
});