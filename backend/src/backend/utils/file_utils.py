import os

def is_audio_file(file_path):
    audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma']
    _, extension = os.path.splitext(file_path)
    return extension.lower() in audio_extensions
