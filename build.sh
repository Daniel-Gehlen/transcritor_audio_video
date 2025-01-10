#!/bin/bash

# Atualiza a lista de pacotes
echo "Atualizando lista de pacotes..."
apt-get update

# Instala o FFmpeg
echo "Instalando FFmpeg..."
apt-get install -y ffmpeg

# Verifica se o FFmpeg foi instalado corretamente
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg instalado com sucesso!"
else
    echo "Erro ao instalar FFmpeg."
    exit 1
fi