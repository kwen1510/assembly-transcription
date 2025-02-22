import streamlit as st
from transcribe import upload_file, transcribe_audio, poll_transcription
import time
from zipfile import ZipFile
from io import BytesIO

# Load secrets
SECRET_KEY = st.secrets["general"]["SECRET_KEY"]
ASSEMBLY_AI_API = st.secrets["general"]["ASSEMBLY_AI_API"]

# App header
st.header("Transcription Tool")
st.subheader("Generate transcriptions with AssemblyAI. You have 3 hours of free conversion per month.")

# Password input
password = st.text_input("Enter the application password", type="password")

if password == SECRET_KEY:
    # File uploader
    uploaded_files = st.file_uploader("Please upload your audio files", accept_multiple_files=True, type=['mp3', 'wav', 'm4a'])

    if uploaded_files:
        # Create an in-memory ZIP file
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            for uploaded_file in uploaded_files:
                # Upload file to AssemblyAI
                upload_url = upload_file(uploaded_file, ASSEMBLY_AI_API)
                
                # Initiate transcription
                transcription_id = transcribe_audio(upload_url, ASSEMBLY_AI_API)
                
                # Poll for transcription completion
                st.write(f"Transcribing {uploaded_file.name}...")
                progress_bar = st.progress(0)
                while True:
                    transcription_result = poll_transcription(transcription_id, ASSEMBLY_AI_API)
                    if transcription_result['status'] == 'completed':
                        break
                    elif transcription_result['status'] == 'failed':
                        st.error(f"Transcription failed for {uploaded_file.name}.")
                        break
                    time.sleep(5)
                    progress_bar.progress(min(progress_bar.progress + 10, 100))
                
                if transcription_result['status'] == 'completed':
                    # Save transcription to ZIP
                    transcription_text = transcription_result['text']
                    file_name = uploaded_file.name.rsplit('.', 1)[0] + '.txt'
                    zf.writestr(file_name, transcription_text)
                    st.success(f"Transcription for {uploaded_file.name} completed.")

        # Provide download of ZIP file
        zip_buffer.seek(0)
        st.download_button(
            label="Download All Transcriptions",
            data=zip_buffer,
            file_name="transcriptions.zip",
            mime="application/zip"
        )
else:
    st.error("Incorrect password. Please try again.")
