const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

module.exports = async (req, res) => {
    if (req.method === 'POST') {
        const file = req.files.file;
        const inputPath = path.join('/tmp', file.name);
        const outputPath = path.join('/tmp', 'converted.mp3');

        // Salva o arquivo temporariamente
        fs.writeFileSync(inputPath, file.data);

        // Converte o arquivo usando FFmpeg
        exec(`ffmpeg -i ${inputPath} ${outputPath}`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Erro na conversão: ${stderr}`);
                return res.status(500).send('Erro na conversão do arquivo.');
            }

            // Lê o arquivo convertido e envia como resposta
            const convertedFile = fs.readFileSync(outputPath);
            res.setHeader('Content-Type', 'audio/mpeg');
            res.setHeader('Content-Disposition', 'attachment; filename="converted.mp3"');
            res.send(convertedFile);

            // Remove os arquivos temporários
            fs.unlinkSync(inputPath);
            fs.unlinkSync(outputPath);
        });
    } else {
        res.status(405).send('Método não permitido.');
    }
};