import requests
import time

def get_url(token, data):
    """
    Uploads the audio file to AssemblyAI and returns the URL of the uploaded file.
    """
    headers = {'authorization': token}
    response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=data)
    response.raise_for_status()
    url = response.json()["upload_url"]
    print("Uploaded file and obtained temporary URL.")
    return url

def get_transcribe_id(token, url, speakers_expected=None):
    """
    Initiates transcription with speaker diarization and returns the transcription ID.
    """
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_payload = {
        "audio_url": url,
        "speaker_labels": True
    }
    if speakers_expected:
        json_payload["speakers_expected"] = speakers_expected

    headers = {
        "authorization": token,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json_payload, headers=headers)
    response.raise_for_status()
    transcribe_id = response.json()['id']
    print("Transcription request submitted; file is currently queued.")
    return transcribe_id

def upload_file(file_obj, token, speakers_expected=None):
    """
    Uploads the file and initiates transcription with speaker diarization.
    """
    file_url = get_url(token, file_obj)
    transcribe_id = get_transcribe_id(token, file_url, speakers_expected)
    return transcribe_id

def get_transcription_result(token, transcribe_id):
    """
    Polls the transcription result until completion and returns the result.
    """
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcribe_id}"
    headers = {"authorization": token}
    while True:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        result = response.json()
        if result['status'] == 'completed':
            print("Transcription completed.")
            return result
        elif result['status'] == 'failed':
            raise RuntimeError("Transcription failed.")
        else:
            print("Transcription processing...")
            time.sleep(5)

def write_srt(token, transcribe_id):
    """
    Retrieves the SRT file for the given transcription ID.
    """
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcribe_id}/srt"
    headers = {"authorization": token}
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    srt_content = response.text
    print("Retrieved SRT content.")
    return srt_content
