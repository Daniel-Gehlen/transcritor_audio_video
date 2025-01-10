document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/convert', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById('status').textContent = data.message;
            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = `/download/${file.name.split('.')[0]}.gif`;
            downloadLink.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });
});