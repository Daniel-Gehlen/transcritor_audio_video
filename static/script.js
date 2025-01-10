document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById('status').textContent = data.message;
            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = `/download/${file.name.split('.')[0]}`;
            downloadLink.style.display = 'block';
        } else if (data.error) {
            document.getElementById('status').textContent = data.error;
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });
});