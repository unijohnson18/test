from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import base64
import logging

app = Flask(__name__)
load_dotenv()

# Настройка логирования в консоль
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('audio_server')

PORT = int(os.getenv('SERVER_PORT', 5055))
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Files in directory: {os.listdir('.')}")

        if 'audio' not in request.files:
            logger.error("No audio file in request")
            return {'message': 'Waiting for audio file'}, 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            logger.error("Empty filename")
            return {'message': 'No file selected'}, 400

        filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f"Saving uploaded file to: {audio_path}")
        audio_file.save(audio_path)

        test_mp3_path = os.path.join(os.getcwd(), 'song.mp3')
        test_txt_path = os.path.join(os.getcwd(), 'song.txt')

        logger.info(f"Reading files from: {test_mp3_path} and {test_txt_path}")

        with open(test_mp3_path, 'rb') as mp3_file:
            processed_audio = base64.b64encode(mp3_file.read()).decode('utf-8')

        with open(test_txt_path, 'rb') as txt_file:
            lyrics = base64.b64encode(txt_file.read()).decode('utf-8')

        return {
            'audio': processed_audio,
            'lyrics': lyrics
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {'message': 'Processing...'}, 500


if __name__ == '__main__':
    logger.info(f"Server starting on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)