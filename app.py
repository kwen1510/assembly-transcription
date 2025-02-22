import streamlit as st
import requests
import time
import io
import os

# AssemblyAI API key (Use your actual key)
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
password = st.text_input("Enter a password", type="password")

# File uploader
uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "mp4"])

if uploaded_file and password == SECRET_KEY:
    st.audio(uploaded_file, format="audio/mp3")
    
    if st.button("Transcribe Audio"):
        with st.spinner("Uploading file..."):
            # Convert uploaded file into a file-like object
            file_bytes = io.BytesIO(uploaded_file.getvalue())
            files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}

            # Upload file to AssemblyAI
            response = requests.post(UPLOAD_URL, headers=headers, files=files)

            if response.status_code == 200:
                audio_url = response.json()["upload_url"]
                st.success("✅ File uploaded successfully.")
            else:
                st.error("❌ Failed to upload file.")
                st.stop()

        with st.spinner("Requesting transcription..."):
            response = requests.post(
                TRANSCRIPT_URL,
                headers=headers,
                json={"audio_url": audio_url, "speaker_labels": True},
            )

            if response.status_code == 200:
                transcript_id = response.json()["id"]
                st.success(f"📋 Transcription request sent (ID: {transcript_id})")
            else:
                st.error("❌ Failed to request transcription.")
                st.stop()

        # Polling for transcript completion
        st.write("⏳ Transcription in progress...")
        status = "queued"
        while status not in ["completed", "failed"]:
            time.sleep(5)  # Wait before polling again
            response = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers)
            transcript_data = response.json()
            status = transcript_data["status"]

            if status == "completed":
                transcript_text = transcript_data["text"]
                utterances = transcript_data.get("utterances", [])

                st.subheader("🔊 Transcription Result:")
                st.write(transcript_text)

                # Show speaker labels if available
                if utterances:
                    st.subheader("🗣️ Speaker Breakdown:")
                    for utterance in utterances:
                        st.write(f"**Speaker {utterance['speaker']}**: {utterance['text']}")

                # Download transcript
                transcript_file = "transcript.txt"
                with open(transcript_file, "w") as f:
                    f.write(transcript_text)

                with open(transcript_file, "rb") as f:
                    st.download_button("📥 Download Transcript", f, file_name="transcript.txt")

                os.remove(transcript_file)
                st.success("✅ Transcription Completed!")

            elif status == "failed":
                st.error("❌ Transcription failed.")
                break

            else:
                st.write("⏳ Processing... Please wait.")
