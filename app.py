import streamlit as st
import requests
import os

# AssemblyAI API key
API_KEY = st.secrets["ASSEMBLY_AI_API"]

# AssemblyAI upload endpoint
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
headers = {"authorization": API_KEY}

# Streamlit file uploader
uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"])

if uploaded_file:
    st.audio(uploaded_file)

    if st.button("Transcribe Audio"):
        with st.spinner("Uploading file..."):
            # Save the uploaded file temporarily
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Open the saved file for reading in binary mode
            with open(uploaded_file.name, "rb") as f:
                response = requests.post(UPLOAD_URL, headers=headers, files={"file": f})

            # Remove the temporary file after uploading
            os.remove(uploaded_file.name)

            if response.status_code == 200:
                audio_url = response.json()["upload_url"]
                st.success("File uploaded successfully.")
                # Proceed with transcription request using 'audio_url'
            else:
                st.error("Failed to upload file.")
