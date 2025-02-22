import streamlit as st
import requests
import time
import zipfile
import tempfile
from io import BytesIO

# AssemblyAI API endpoints
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

# Streamlit UI
st.header("🎬 Subtitling Tool")
st.subheader("Generate subtitles with AssemblyAI (3 free hours/month)")

api_key = st.text_input("🔑 Enter your AssemblyAI API key", type="password")

fileObjects = st.file_uploader("📂 Upload your audio/video files", accept_multiple_files=True)

if fileObjects and api_key:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create ZIP file to store subtitles
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            
            for fileObject in fileObjects:
                # Save uploaded file to temporary storage
                temp_file_path = f"{temp_dir}/{fileObject.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(fileObject.getvalue())

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
                progress_bar = st.progress(0)
                status = "queued"

                while status not in ["completed", "failed"]:
                    time.sleep(5)  # Poll every 5 seconds
                    response = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers)
                    result = response.json()
                    status = result.get("status", "")

                    # Update progress
                    progress_bar.progress(min(progress_bar.progress + 10, 100))

                if status == "failed":
                    st.error(f"❌ Transcription failed for {fileObject.name}")
                    continue

                # Extract transcript text
                transcript_text = result.get("text", "")
                if not transcript_text:
                    st.error(f"❌ No transcript generated for {fileObject.name}")
                    continue

                # Convert to SRT format
                srt_text = "\n".join([f"{i}\n00:00:0{i//2},000 --> 00:00:0{i//2 + 1},000\n{line}"
                                      for i, line in enumerate(transcript_text.split('. '), 1)])

                # Add SRT file to ZIP
                file_name = fileObject.name.rsplit(".", 1)[0] + ".srt"
                zf.writestr(file_name, srt_text)
                st.success(f"📜 Subtitle file for {fileObject.name} created")

        # Provide ZIP download button
        zip_buffer.seek(0)
        st.download_button("📥 Download All Subtitles", zip_buffer, "subtitles.zip", "application/zip")
        st.success("🎉 All subtitles created!")
