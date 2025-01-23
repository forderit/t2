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

# Configure Streamlit
st.set_page_config(
    page_title="Real-Time Transcription",
    page_icon="🎙️"
)

# Session state
if 'text' not in st.session_state:
    st.session_state['text'] = 'Listening...'
    st.session_state['run'] = False
    st.session_state['debug_log'] = []

# Web user interface
st.title('🎙️ Real-Time Transcription App')

# Add debug log display
if st.checkbox('Show Debug Info'):
    st.code('\n'.join(st.session_state.debug_log))

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
            <button onclick="initializeConnection()" id="startBtn">Start Recording</button>
            <button onclick="stopRecording()" id="stopBtn" disabled>Stop Recording</button>
            <div id="statusLog" style="margin-top: 10px; color: gray;"></div>
            <div id="connectionStatus" style="margin-top: 5px; font-size: 12px;"></div>
        </div>

        <script>
        let mediaRecorder;
        let audioChunks = [];
        let ws;
        let isConnected = false;
        const API_KEY = '0c61b4cc27bf405c856cf0796e6b7f97';

        function updateConnectionStatus(message, isError = false) {
            const statusEl = document.getElementById('connectionStatus');
            statusEl.style.color = isError ? 'red' : 'green';
            statusEl.textContent = message;
        }

        function logStatus(message) {
            console.log(message);
            document.getElementById('statusLog').innerText = message;
            window.parent.postMessage({
                type: 'streamlit:message',
                debug: message
            }, '*');
        }

        async function initializeConnection() {
            try {
                logStatus('Initializing connection...');
                updateConnectionStatus('Connecting...', false);

                const wsUrl = 'wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000';
                ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    logStatus('Connection established - sending auth...');
                    // Send authentication message immediately after connection
                    ws.send(JSON.stringify({
                        'session_begins': true,
                        'token': API_KEY
                    }));
                };

                let authenticationSuccessful = false;

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Received message:', data);
                        
                        if (!authenticationSuccessful) {
                            if (data.message_type === 'SessionBegins') {
                                authenticationSuccessful = true;
                                logStatus('Authentication successful - starting recording...');
                                startRecording();
                            } else if (data.error) {
                                logStatus(`Authentication error: ${data.error}`);
                                updateConnectionStatus('Auth Error: ' + data.error, true);
                            }
                        } else if (data.message_type === 'FinalTranscript') {
                            window.parent.postMessage({
                                type: 'streamlit:message',
                                text: data.text
                            }, '*');
                        }
                    } catch (error) {
                        logStatus(`Error processing message: ${error.message}`);
                    }
                };

                ws.onerror = (error) => {
                    logStatus(`WebSocket Error: ${error.message || 'Unknown error'}`);
                    updateConnectionStatus('Connection Error', true);
                    console.error('WebSocket Error:', error);
                };

                ws.onclose = (event) => {
                    isConnected = false;
                    let closeReason = '';
                    if (event.code === 4001) {
                        closeReason = 'Authentication Failed';
                    } else if (event.code === 1000) {
                        closeReason = 'Normal Closure';
                    } else {
                        closeReason = `Code: ${event.code}`;
                    }
                    logStatus(`WebSocket Closed (${closeReason})`);
                    updateConnectionStatus('Disconnected: ' + closeReason, true);
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                };

            } catch (error) {
                logStatus(`Setup Error: ${error.message}`);
                updateConnectionStatus('Connection Failed', true);
                console.error('Setup Error:', error);
            }
        }

        async function startRecording() {
            try {
                logStatus('Requesting microphone access...');
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                logStatus('Microphone access granted');
                isConnected = true;
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus',
                    audioBitsPerSecond: 128000
                });
                
                mediaRecorder.ondataavailable = async (event) => {
                    try {
                        if (event.data.size > 0 && isConnected && ws.readyState === WebSocket.OPEN) {
                            const reader = new FileReader();
                            reader.onloadend = () => {
                                try {
                                    const base64data = reader.result.split(',')[1];
                                    ws.send(JSON.stringify({
                                        "audio_data": base64data
                                    }));
                                } catch (error) {
                                    logStatus(`Error sending audio: ${error.message}`);
                                }
                            };
                            reader.readAsDataURL(event.data);
                        }
                    } catch (error) {
                        logStatus(`Error handling audio data: ${error.message}`);
                    }
                };

                mediaRecorder.onstart = () => {
                    logStatus('Recording started');
                    updateConnectionStatus('Recording Active', false);
                };

                mediaRecorder.onerror = (error) => {
                    logStatus(`MediaRecorder error: ${error.message}`);
                };
                
                mediaRecorder.start(250);
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
            } catch (error) {
                logStatus(`Microphone error: ${error.message}`);
                updateConnectionStatus('Microphone Error', true);
                console.error('Microphone Error:', error);
                alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
            }
        }

        function stopRecording() {
            try {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    logStatus('Recording stopped');
                }
                if (ws) {
                    ws.close(1000, 'User stopped recording');
                    logStatus('Connection closed');
                }
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                updateConnectionStatus('Stopped', false);
            } catch (error) {
                logStatus(`Error stopping recording: ${error.message}`);
            }
        }
        </script>
        """,
        height=150,
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