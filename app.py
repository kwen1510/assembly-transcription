import streamlit as st
import assemblyai as aai
import json

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
    uploaded_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a", "mp4", "mov"])

    # Select transcription mode
    mode = st.radio(
        "Select Transcription Mode",
        ("Standard Transcription", "Transcription with Speaker Diarization")
    )

    # Speaker selection (only for diarization mode)
    speakers_expected = None
    if mode == "Transcription with Speaker Diarization":
        speakers_expected = st.number_input(
            "Expected number of speakers",
            min_value=1, max_value=10, step=1, value=3
        )

    # Transcribe button
    if st.button("Transcribe") and uploaded_file is not None:
        # Configure transcription settings
        config = aai.TranscriptionConfig(
            speaker_labels=(mode == "Transcription with Speaker Diarization"),
            speakers_expected=speakers_expected if mode == "Transcription with Speaker Diarization" else None
        )

        # Transcribe the uploaded audio file
        with st.spinner("Transcribing..."):
            transcript = transcriber.transcribe(uploaded_file, config)

        # Check for errors
        if transcript.status == aai.TranscriptStatus.error:
            st.error(f"Transcription failed: {transcript.error}")
        else:
            # If speaker diarization is selected, show only diarization output
            if mode == "Transcription with Speaker Diarization":
                st.header("Speaker Diarization Output")
                diarization_data = []
                for utterance in transcript.utterances:
                    speaker = utterance.speaker
                    start_time = utterance.start / 1000  # Convert to seconds
                    end_time = utterance.end / 1000      # Convert to seconds
                    text = utterance.text
                    diarization_data.append({
                        "speaker": speaker,
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": text
                    })
                    st.write(f"**Speaker {speaker} [{start_time:.2f}s - {end_time:.2f}s]:** {text}")

                # Download button for JSON output
                json_output = json.dumps(diarization_data, indent=4)
                st.download_button(
                    label="Download JSON Output",
                    data=json_output,
                    file_name="transcription.json",
                    mime="application/json"
                )
            else:
                # Standard transcription output (Collapsible)
                with st.expander("Show/Hide Transcription"):
                    st.header("Transcription Output")
                    st.write(transcript.text)
else:
    st.error("Incorrect password. Please try again.")
