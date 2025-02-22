import streamlit as st
from transcribe import upload_file, get_transcription_result, write_srt
from io import BytesIO
from zipfile import ZipFile
import time

# Load secrets
SECRET_KEY = st.secrets["general"]["SECRET_KEY"]
ASSEMBLY_AI_API = st.secrets["general"]["ASSEMBLY_AI_API"]

# App header
st.header("Transcription Tool with Speaker Diarization")
st.subheader("Generate transcriptions with speaker labels using AssemblyAI.")

# Password input
password = st.text_input("Enter the application password", type="password")

if password == SECRET_KEY:
    # File uploader
    uploaded_files = st.file_uploader("Upload your audio files", accept_multiple_files=True, type=['mp3', 'wav', 'm4a'])

    # Optional: Number of speakers
    speakers_expected = st.number_input("Expected number of speakers (optional)", min_value=1, step=1, value=2)

    if uploaded_files:
        # Create an in-memory ZIP file
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            for uploaded_file in uploaded_files:
                # Upload file and initiate transcription
                st.write(f"Processing {uploaded_file.name}...")
                transcribe_id = upload_file(uploaded_file, ASSEMBLY_AI_API, speakers_expected)

                # Poll for transcription completion
                progress_bar = st.progress(0)
                while True:
                    result = get_transcription_result(ASSEMBLY_AI_API, transcribe_id)
                    if result['status'] == 'completed':
                        break
                    time.sleep(5)
                    progress_bar.progress(min(progress_bar.progress + 10, 100))

                # Retrieve SRT content
                srt_content = write_srt(ASSEMBLY_AI_API, transcribe_id)

                # Save SRT to ZIP
                file_name = uploaded_file.name.rsplit('.', 1)[0] + '.srt'
                zf.writestr(file_name, srt_content)
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
