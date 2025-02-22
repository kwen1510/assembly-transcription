import streamlit as st
import requests
import time
import tempfile
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
password = st.text_input("Enter the password", type="password", key="password")

# File uploader
uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "mp4"])

if uploaded_file and password == SECRET_KEY:
    st.audio(uploaded_file)

    if st.button("Transcribe Audio"):
        with st.spinner("Saving file..."):
            # Save the uploaded file properly
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name  # Store the temp file path

            st.success(f"✅ File saved: {temp_file_path}")

        with st.spinner("Uploading file..."):
            try:
                with open(temp_file_path, "rb") as f:
                    files = {"file": (uploaded_file.name, f, uploaded_file.type)}  # Correct format
                    response = requests.post(UPLOAD_URL, headers=headers, files=files)

                if response.status_code == 200:
                    audio_url = response.json()["upload_url"]
                    st.success("✅ File uploaded successfully.")
                else:
                    st.error(f"❌ Failed to upload file. Error: {response.text}")
                    os.remove(temp_file_path)  # Delete temp file
                    st.stop()
            except Exception as e:
                st.error(f"❌ An error occurred during upload: {e}")
                os.remove(temp_file_path)  # Clean up
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
                st.error(f"❌ Failed to request transcription. Error: {response.text}")
                os.remove(temp_file_path)  # Clean up
                st.stop()

        # Polling for transcript completion
        st.write("⏳ Transcription in progress...")
        status = "queued"
        while status not in ["completed", "failed"]:
            time.sleep(5)
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

                # Provide transcript download button
                st.download_button(
                    label="📥 Download Transcript",
                    data=transcript_text,
                    file_name="transcript.txt",
                    mime="text/plain",
                )

                st.success("✅ Transcription Completed!")

            elif status == "failed":
                st.error("❌ Transcription failed.")
                break

            else:
                st.write("⏳ Processing... Please wait.")

        # Delete the temporary file after processing
        os.remove(temp_file_path)
        st.write(f"🗑️ Deleted temporary file: {temp_file_path}")
