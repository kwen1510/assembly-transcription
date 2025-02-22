import streamlit as st
import time
import zipfile
from io import BytesIO
import tempfile
import requests

# AssemblyAI API endpoints
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

st.header("🎬 Subtitling Tool")
st.subheader("Generate your subtitles with AssemblyAI. You are given 3 hours of free conversion per month.")

api_key = st.text_input("🔑 Enter your AssemblyAI API key", type="password")

fileObjects = st.file_uploader("📂 Upload your files", accept_multiple_files=True)

if fileObjects and api_key:
    # Create a ZIP buffer
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

        for fileObject in fileObjects:
            # Save uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{fileObject.name.split('.')[-1]}") as temp_file:
                temp_file.write(fileObject.getvalue())
                temp_file_path = temp_file.name  # Store the temp file path

            st.write(f"📤 Uploading: {fileObject.name}")

            # Upload to AssemblyAI
            with open(temp_file_path, "rb") as f:
                headers = {"authorization": api_key}
                response = requests.post(UPLOAD_URL, headers=headers, files={"file": f})

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
            sleep_duration = 1
            percent_complete = 0
            progress_bar = st.progress(percent_complete)
            st.text("Currently in queue")

            result = {}
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

            # Delete temp file after processing
            os.remove(temp_file_path)

    # Provide ZIP download button
    zip_buffer.seek(0)
    st.download_button("📥 Download All Subtitles", zip_buffer, "subtitles.zip", "application/zip")

    st.success("🎉 All subtitles created!")
