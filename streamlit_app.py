import streamlit as st
import websockets
import asyncio
import base64
import json
import os
from pathlib import Path
import streamlit.components.v1 as components
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from Streamlit secrets
API_KEY = st.secrets["api_key"]

# Configure Streamlit
st.set_page_config(
    page_title="Real-Time Transcription",
    page_icon="🎙️"
)

# Session state
if 'text' not in st.session_state:
    st.session_state['text'] = 'Listening...'
    st.session_state['run'] = False

# Web user interface
st.title('🎙️ Real-Time Transcription App')

with st.expander('About this App'):
    st.markdown('''
    This Streamlit app uses the AssemblyAI API to perform real-time transcription.
    
    Access your microphone through the browser and get real-time transcription!
    ''')

# Create a custom component for microphone access
def mic_component():
    return components.html(
        f"""
        <div>
            <button onclick="startRecording()" id="startBtn">Start Recording</button>
            <button onclick="stopRecording()" id="stopBtn" disabled>Stop Recording</button>
            <div id="statusLog" style="margin-top: 10px; color: gray;"></div>
        </div>

        <script>
        let mediaRecorder;
        let audioChunks = [];
        let ws;

        function logStatus(message) {{
            console.log(message);
            document.getElementById('statusLog').innerText = message;
        }}

        async function startRecording() {{
            try {{
                // First request microphone permission
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                logStatus('Microphone access granted, connecting to API...');

                // Create WebSocket connection
                ws = new WebSocket('wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000');

                // Set up WebSocket handlers
                ws.onopen = () => {{
                    logStatus('Connection established');
                    ws.send(JSON.stringify({{
                        "session_begins": true,
                        "token": "{API_KEY}"
                    }}));
                    startMediaRecorder(stream);
                }};

                ws.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    if (data.message_type === 'FinalTranscript') {{
                        window.parent.postMessage({{
                            type: 'streamlit:message',
                            text: data.text
                        }}, '*');
                    }}
                }};

                ws.onerror = (error) => {{
                    logStatus(`Error: ${{error.message}}`);
                    console.error('WebSocket Error:', error);
                }};

                ws.onclose = (event) => {{
                    logStatus('Connection closed');
                    stopMediaRecorder();
                }};

            }} catch (error) {{
                logStatus(`Error: ${{error.message}}`);
                console.error('Setup Error:', error);
            }}
        }}

        function startMediaRecorder(stream) {{
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = async (event) => {{
                if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {{
                    const reader = new FileReader();
                    reader.onloadend = () => {{
                        const base64data = reader.result.split(',')[1];
                        ws.send(JSON.stringify({{
                            "audio_data": base64data
                        }}));
                    }};
                    reader.readAsDataURL(event.data);
                }}
            }};

            mediaRecorder.start(250);
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            logStatus('Recording started');
        }}

        function stopMediaRecorder() {{
            if (mediaRecorder && mediaRecorder.state === 'recording') {{
                mediaRecorder.stop();
            }}
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.close();
            }}
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }}

        function stopRecording() {{
            logStatus('Stopping recording...');
            stopMediaRecorder();
        }}
        </script>
        """,
        height=100,
    )

# Display the microphone component
mic_component()

# Display transcription results
st.markdown("### Transcription")
st.markdown(st.session_state.text)

# If there's a transcription file, offer download
if Path('transcription.txt').is_file():
    st.markdown('### Download')
    with open('transcription.txt', 'r') as f:
        st.download_button(
            label="Download transcription",
            data=f,
            file_name='transcription_output.txt',
            mime='text/plain'
        )