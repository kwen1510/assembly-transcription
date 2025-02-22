import streamlit as st
import assemblyai as aai

# Load API key from Streamlit secrets
aai.settings.api_key = st.secrets["ASSEMBLY_AI_API"]

# Initialize the transcriber
transcriber = aai.Transcriber()

# Streamlit app
st.title("AssemblyAI Transcription App")

# Password input
password = st.text_input("Enter the application password", type="password")

if password == st.secrets["SECRET_KEY"]:
    # File uploader
    uploaded_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        # Select transcription mode
        mode = st.radio(
            "Select Transcription Mode",
            ("Standard Transcription", "Transcription with Speaker Diarization")
        )

        # Transcription configuration
        if mode == "Transcription with Speaker Diarization":
            config = aai.TranscriptionConfig(speaker_labels=True)
        else:
            config = aai.TranscriptionConfig()

        # Transcribe the uploaded audio file
        with st.spinner("Transcribing..."):
            transcript = transcriber.transcribe(uploaded_file, config)

        # Check for errors
        if transcript.status == aai.TranscriptStatus.error:
            st.error(f"Transcription failed: {transcript.error}")
        else:
            # Display the transcribed text
            st.header("Transcription")
            st.write(transcript.text)

            # If speaker labels are enabled, display utterances
            if mode == "Transcription with Speaker Diarization":
                st.header("Speaker Diarization")
                for utterance in transcript.utterances:
                    speaker = utterance.speaker
                    start_time = utterance.start / 1000  # Convert to seconds
                    end_time = utterance.end / 1000      # Convert to seconds
                    text = utterance.text
                    st.write(f"**Speaker {speaker} [{start_time:.2f}s - {end_time:.2f}s]:** {text}")
else:
    st.error("Incorrect password. Please try again.")
