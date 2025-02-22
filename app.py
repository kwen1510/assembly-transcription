import streamlit as st
import requests
import time
import os

# AssemblyAI API key and secret key
API_KEY = st.secrets["ASSEMBLY_AI_API"]
SECRET_KEY = st.secrets["SECRET_KEY"]

# AssemblyAI endpoints
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

headers = {"authorization": API_KEY}

# Streamlit UI
st.title("🎙️ Audio Transcription with AssemblyAI")
st.markdown("Upload an audio file and get a transcription.")

# Password field
password = st.text_input("Enter the password", type="password")

# File uploader
uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "mp4"])

if uploaded_file and password == SECRET_KEY:
    st.audio(uploaded_file)

    if st.button("Transcribe Audio"):
        with st.spinner("Processing..."):
            # Save the uploaded file locally
            file_path = os.path.join("tempDir", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Upload the file to AssemblyAI
            with open(file_path, "rb") as f:
                response = requests.post(UPLOAD_URL, headers=headers, files={"file": f})

            if response.status_code == 200:
                audio_url = response.json()["upload_url"]
                st.success("File uploaded successfully.")

                # Request transcription
                response = requests.post(
                    TRANSCRIPT_URL,
                    headers=headers,
                    json={"audio_url": audio_url, "speaker_labels": True},
                )

                if response.status_code == 200:
                    transcript_id = response.json()["id"]
                    st.success(f"Transcription requested (ID: {transcript_id})")

                    # Polling for transcription completion
                    status = "queued"
                    while status not in ["completed", "failed"]:
                        time.sleep(5)
                        response = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers)
                        status = response.json()["status"]

                    if status == "completed":
                        transcript_text = response.json()["text"]
                        st.subheader("Transcription Result:")
                        st.write(transcript_text)

                        # Provide download link
                        st.download_button(
                            label="Download Transcript",
                            data=transcript_text,
                            file_name="transcript.txt",
                            mime="text/plain",
                        )
                    else:
                        st.error("Transcription failed.")
                else:
                    st.error("Failed to request transcription.")
            else:
                st.error("Failed to upload file.")

            # Delete the local file
            os.remove(file_path)
