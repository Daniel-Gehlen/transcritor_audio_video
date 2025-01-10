document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Erro ao enviar o arquivo.');
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Exibe o status de sucesso
        document.getElementById('status').textContent = 'Arquivo processado com sucesso!';

        // Faz o download do arquivo convertido
        const link = document.createElement('a');
        link.href = `data:text/plain;base64,${data.file}`;
        link.download = 'transcricao.txt';
        link.click();
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('status').textContent = error.message;
    }
});