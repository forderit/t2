import streamlit as st
import websockets
import asyncio
import base64
import json
import os
from pathlib import Path
import streamlit.components.v1 as components

# Get port from environment variable
port = int(os.environ.get("PORT", 8501))

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
        """
        <div>
            <button onclick="startRecording()" id="startBtn">Start Recording</button>
            <button onclick="stopRecording()" id="stopBtn">Stop Recording</button>
        </div>

        <script>
        let mediaRecorder;
        let audioChunks = [];
        let ws;

        async function setupWebSocket() {
            ws = new WebSocket('wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000');
            
            ws.onopen = () => {
                console.log('WebSocket Connected');
                ws.send(JSON.stringify({
                    "session_begins": true
                }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.message_type === 'FinalTranscript') {
                    // Send message to Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:message',
                        text: data.text
                    }, '*');
                }
            };
        }

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = async (event) => {
                    audioChunks.push(event.data);
                    if (audioChunks.length > 0) {
                        const audioBlob = new Blob(audioChunks);
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {
                            const base64data = reader.result.split(',')[1];
                            if (ws && ws.readyState === WebSocket.OPEN) {
                                ws.send(JSON.stringify({
                                    "audio_data": base64data
                                }));
                            }
                        };
                        audioChunks = [];
                    }
                };
                
                mediaRecorder.start(100);
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                setupWebSocket();
            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                if (ws) ws.close();
            }
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
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