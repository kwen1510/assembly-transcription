import streamlit as st
import requests
import time
import tempfile
import os
import zipfile
from io import BytesIO

# AssemblyAI API key and secret key
API_KEY = st.secrets["ASSEMBLY_AI_API"]
SECRET_KEY = st.secrets["SECRET_KEY"]

# AssemblyAI endpoints
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

headers = {"authorization": API_KEY}

# Streamlit UI
st.title("🎬 Subtitling Tool")
st.subheader("Generate subtitles with AssemblyAI. You are given 3 hours of free conversion per month.")

# Password field
password = st.text_input("🔑 Enter your password", type="password", key="password")

# File uploader (Multiple files)
fileObjects = st.file_uploader("📂 Please upload your file(s)", accept_multiple_files=True)

if fileObjects and password == SECRET_KEY:
    # Create a ZIP buffer
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

        for fileObject in fileObjects:
            st.write(f"📤 Uploading: {fileObject.name}")

            # Save file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{fileObject.name.split('.')[-1]}") as temp_file:
                temp_file.write(fileObject.getvalue())
                temp_file_path = temp_file.name  # Store temp file path

            # Upload to AssemblyAI
            with open(temp_file_path, "rb") as f:
                response = requests.post(UPLOAD_URL, headers=headers, files={"file": f})

            # Delete temp file after upload
            os.remove(temp_file_path)

            if response.status_code != 200:
                st.error(f"❌ Failed to upload {fileObject.name}")
                continue

            audio_url = response.json()["upload_url"]
            st.success(f"✅ Uploaded: {fileObject.name}")

            # Request transcription
            payload = {"audio_url": audio_url, "speaker_labels": True, "format_text": True}
            response = requests.post(TRANSCRIPT_URL, headers=headers, json=payload)

            if response.status_code != 200:
                st.error(f"❌ Failed to request transcription for {fileObject.name}")
                continue

            transcript_id = response.json()["id"]
            st.write(f"⏳ Transcription in progress for {fileObject.name}")

            # Polling for transcript completion
            result = {}
            sleep_duration = 1
            percent_complete = 0
            progress_bar = st.progress(percent_complete)
            st.text("Currently in queue")

            while result.get("status") != "processing":
                percent_complete += sleep_duration
                time.sleep(sleep_duration)
                progress_bar.progress(percent_complete / 10)
                response = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers)
                result = response.json()

            sleep_duration = 0.01
            for percent in range(percent_complete, 101):
                time.sleep(sleep_duration)
                progress_bar.progress(percent)

            with st.spinner("Processing..."):
                while result.get("status") != 'completed':
                    time.sleep(2)
                    response = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers)
                    result = response.json()

            # Extract transcript text
            transcript_text = result.get("text", "")
            if not transcript_text:
                st.error(f"❌ No transcript generated for {fileObject.name}")
                continue

            # Convert transcript to SRT format
            srt_text = "\n".join([f"{i}\n00:00:0{i//2},000 --> 00:00:0{i//2 + 1},000\n{line}"
                                  for i, line in enumerate(transcript_text.split('. '), 1)])

            file_name = fileObject.name.split('.')[0] + ".srt"
            st.write(f"✅ Subtitle file for {file_name} created")

            # Write subtitle into ZIP file
            zf.writestr(file_name, srt_text)

    # Provide ZIP download button
    zip_buffer.seek(0)
    st.download_button("📥 Download All Subtitles", zip_buffer, "subtitles.zip", "application/zip")

    st.success("🎉 All subtitles created!")
