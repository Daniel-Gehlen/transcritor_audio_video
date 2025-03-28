# Transcrição de Áudio/Vídeo para Texto

## 📝 Descrição

Este projeto é uma aplicação web que permite transcrever arquivos de áudio e vídeo para texto, utilizando tecnologias modernas de processamento de mídia e reconhecimento de fala.

## 🛠 Tecnologias Utilizadas

- **Backend**:
  - Python 3.x
  - Flask (framework web)
  - SpeechRecognition (para reconhecimento de voz)
  - MoviePy (para extração de áudio de vídeos)
  - Werkzeug (para manipulação de arquivos e uploads)

- **Frontend**:
  - HTML5, CSS3, JavaScript
  - Fetch API para comunicação assíncrona
  - EventSource para atualizações de progresso (SSE)

- **Infraestrutura**:
  - Sistema de upload em chunks (partes) para arquivos grandes
  - Processamento assíncrono em threads separadas
  - Armazenamento temporário em disco

## ⚠️ Limitações

- **Não suporta arquivos WAV** para transcrição direta (o sistema funciona melhor com vídeos ou outros formatos de áudio)
- Limite de tamanho de arquivo: 50MB
- Requer conexão com a internet para o serviço de reconhecimento de voz do Google

## three
```
📁 api/
    📄 transcribe.js
📄 app.py
📄 readme.md
📁 static/
    📄 script.js
    📄 styles.css
📁 templates/
    📄 index.html
📄 vercel.json
📄 wsgi.py import warnings
```

## 🎯 Casos de Uso

1. **Transcrição de palestras e aulas**: Converta gravações de aulas ou palestras em texto para revisão.
2. **Acessibilidade**: Gere legendas automáticas para vídeos.
3. **Jornalismo**: Transcreva entrevistas para facilitar a produção de matérias.
4. **Reuniões**: Converta gravações de reuniões em atas textuais.

## 🚀 Como Instalar e Rodar

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- FFmpeg (para processamento de vídeos)

### Passo a Passo

1. **Clone o repositório**:
   ```bash
   git clone [URL_DO_REPOSITORIO]
   cd [NOME_DO_DIRETORIO]
   ```

2. **Instale o FFmpeg**:
   - No Ubuntu/Debian:
     ```bash
     sudo apt-get install ffmpeg
     ```
   - No macOS (com Homebrew):
     ```bash
     brew install ffmpeg
     ```
   - No Windows: Baixe do site oficial e adicione ao PATH

3. **Crie um ambiente virtual (opcional mas recomendado)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Execute a aplicação**:
   ```bash
   python app.py
   ```

6. **Acesse no navegador**:
   Abra `http://localhost:5000` no seu navegador preferido.

## 🖥 Como Usar

1. Na página inicial, clique em "Selecionar Arquivo" para escolher um arquivo de vídeo ou áudio.
2. Aguarde o upload (arquivos grandes podem demorar).
3. O sistema irá extrair o áudio (se for vídeo) e transcrever para texto.
4. Quando concluído, um link para download da transcrição será disponibilizado.

## 📌 Notas Adicionais

- Arquivos temporários são automaticamente removidos após o processamento.
- Para arquivos muito grandes, considere dividi-los antes do upload.
- O serviço de reconhecimento de voz usado é o do Google, que requer internet.

## 📜 Licença

[MIT License] - Consulte o arquivo LICENSE para mais detalhes.
