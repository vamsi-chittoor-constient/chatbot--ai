import { useState, useRef, useCallback, useEffect } from 'react';

export function useVoiceChat(sessionId, onEvent) {
    const [isConnected, setIsConnected] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isUserSpeaking, setIsUserSpeaking] = useState(false);
    const [isAISpeaking, setIsAISpeaking] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [responseText, setResponseText] = useState('');
    const [error, setError] = useState(null);
    const [voiceModeEnabled, setVoiceModeEnabled] = useState(false);

    const socketRef = useRef(null);
    const audioContextRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const processorRef = useRef(null);
    const audioQueueRef = useRef([]);
    const isPlayingRef = useRef(false);
    const voiceModeEnabledRef = useRef(false);
    const isAISpeakingRef = useRef(false); // Ref for instant access in audio processor
    const currentSourceRef = useRef(null); // Track current playing AudioBufferSource for stop
    const languageRef = useRef('English'); // Track language for reconnect
    const reconnectTimeoutRef = useRef(null); // Track reconnect timeout for cleanup

    const connect = useCallback((language = 'English') => {
        languageRef.current = language; // Store for reconnect

        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (socketRef.current) {
            // Remove onclose BEFORE closing to prevent auto-reconnect from
            // firing when we intentionally close for a language switch / reconnect.
            // Without this, onclose schedules a 3s reconnect that creates an
            // infinite connect-disconnect loop (~4s cycle).
            socketRef.current.onclose = null;
            socketRef.current.close();
        }

        // Use same pattern as useWebSocket - construct URL from window.location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        // Backend WebSocket endpoint is at /api/v1/ws/voice/{session_id}
        const wsUrl = `${protocol}//${host}/api/v1/ws/voice/${sessionId}?language=${encodeURIComponent(language)}`;
        console.log('Connecting to voice WebSocket:', wsUrl);

        try {
            const socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log('Voice WebSocket connected');
                setIsConnected(true);
                setError(null);
            };

            socket.onclose = (event) => {
                console.log('Voice WebSocket disconnected:', event.code, event.reason);
                setIsConnected(false);

                // Only stop mic if voice mode is NOT active
                // (keeps mic running during brief reconnects so audio flows immediately)
                if (!voiceModeEnabledRef.current) {
                    setIsRecording(false);
                    stopMicrophoneStream();
                }

                // Auto-reconnect after 3 seconds (like chat WebSocket)
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('Voice WebSocket auto-reconnecting...');
                    connect(languageRef.current);
                }, 3000);
            };

            socket.onerror = (err) => {
                console.error('Voice WebSocket error:', err);
                setError('Connection error');
                setIsConnected(false);
            };

            socket.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleServerMessage(data);
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };

            socketRef.current = socket;
        } catch (err) {
            console.error('Failed to create WebSocket:', err);
            setError('Failed to connect');
        }
    }, [sessionId]);

    const handleServerMessage = async (data) => {
        switch (data.type) {
            case 'connection_established':
                console.log('Server confirmed connection');
                break;

            case 'speech_started':
                console.log('Server detected speech start');
                setIsUserSpeaking(true);
                break;

            case 'speech_ended':
                console.log('Server detected speech end');
                setIsUserSpeaking(false);
                break;

            case 'processing_start':
                setIsProcessing(true);
                break;

            case 'processing_end':
                setIsProcessing(false);
                break;

            case 'transcript':
                setTranscript(data.text || '');
                break;

            case 'response_text':
                setResponseText(data.text || '');
                break;

            case 'audio_start':
                setIsAISpeaking(true);
                isAISpeakingRef.current = true;
                audioQueueRef.current = [];
                break;

            case 'audio_chunk':
                if (data.audio) {
                    const audioData = base64ToArrayBuffer(data.audio);
                    audioQueueRef.current.push(audioData);
                    // Thread-safe: Only initiate playback if not already playing
                    // isPlayingRef acts as a mutex to prevent concurrent playback
                    if (!isPlayingRef.current) {
                        playNextAudioChunk();
                    }
                }
                break;

            case 'audio_end':
                // Don't immediately set isAISpeaking=false here.
                // Wait until audio queue is fully drained and last chunk finishes playing.
                // Mark that no more chunks are coming.
                audioQueueRef.current._audioEndReceived = true;
                // If nothing is playing and queue is empty, end now
                if (!isPlayingRef.current && audioQueueRef.current.length === 0) {
                    setIsAISpeaking(false);
                    isAISpeakingRef.current = false;
                }
                break;

            case 'agui_event':
                // Forward AG-UI events (menu cards, cart, search results, quick replies, etc.)
                // to the same handler used by chat mode so cards render in the UI.
                // Skip TEXT_MESSAGE events - voice mode handles text display via responseText
                // useEffect in App.jsx. Forwarding them would create duplicate messages.
                if (data.agui && onEvent) {
                    const eventType = data.agui.type;
                    if (eventType !== 'TEXT_MESSAGE_START' &&
                        eventType !== 'TEXT_MESSAGE_CONTENT' &&
                        eventType !== 'TEXT_MESSAGE_END') {
                        console.log('Voice AGUI event:', eventType);
                        onEvent(data.agui);
                    }
                }
                break;

            case 'error':
                console.error('Server error:', data.message);
                setError(data.message);
                break;
        }
    };

    const startMicrophoneStream = async () => {
        try {
            // Request microphone access with enhanced noise handling
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000, // 16kHz for VAD
                    echoCancellation: true,  // Remove echo from speakers
                    noiseSuppression: true,  // Remove background noise
                    autoGainControl: true,   // Normalize volume levels
                    // Advanced constraints for better quality
                    latency: 0.01,           // Low latency for real-time
                    suppressLocalAudioPlayback: true  // Prevent feedback loops
                }
            });

            mediaStreamRef.current = stream;

            // Create audio context
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            }

            const audioContext = audioContextRef.current;
            const source = audioContext.createMediaStreamSource(stream);

            // Create script processor to capture audio
            // Silero VAD requires exactly 512 samples for 16kHz audio
            const processor = audioContext.createScriptProcessor(512, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!voiceModeEnabledRef.current || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
                    return;
                }

                // MUTE MIC: Don't send audio while AI is speaking or processing
                // This prevents echo/feedback and ensures clean turn-taking
                if (isAISpeakingRef.current) {
                    return;
                }

                const inputData = e.inputBuffer.getChannelData(0);

                // Convert Float32 to Int16 PCM
                const pcmData = convertFloat32ToInt16(inputData);
                const base64Data = arrayBufferToBase64(pcmData.buffer);

                // Send to server
                socketRef.current.send(JSON.stringify({
                    type: 'audio_chunk',
                    audio: base64Data
                }));
            };

            source.connect(processor);
            processor.connect(audioContext.destination);
            processorRef.current = processor;

            console.log('Microphone stream started');
            setIsRecording(true);

        } catch (err) {
            console.error('Failed to start microphone:', err);
            setError('Microphone access denied');
        }
    };

    const stopMicrophoneStream = () => {
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }

        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
            mediaStreamRef.current = null;
        }

        setIsRecording(false);
        console.log('Microphone stream stopped');
    };

    const playNextAudioChunk = async () => {
        // Atomically check and dequeue
        // This prevents race conditions when multiple chunks arrive simultaneously
        if (isPlayingRef.current || audioQueueRef.current.length === 0) {
            isPlayingRef.current = false;
            // If audio_end was received and queue is now empty, AI is done speaking
            if (audioQueueRef.current._audioEndReceived && audioQueueRef.current.length === 0) {
                setIsAISpeaking(false);
                isAISpeakingRef.current = false;
                audioQueueRef.current._audioEndReceived = false;
            }
            return;
        }

        // Set mutex BEFORE dequeuing to prevent race condition
        isPlayingRef.current = true;
        const audioData = audioQueueRef.current.shift();

        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            }

            if (audioContextRef.current.state === 'suspended') {
                await audioContextRef.current.resume();
            }

            // Convert Int16 PCM to Float32 for AudioBuffer
            const float32Data = convertInt16ToFloat32(new Int16Array(audioData));
            const audioBuffer = audioContextRef.current.createBuffer(1, float32Data.length, 24000);
            audioBuffer.getChannelData(0).set(float32Data);

            const source = audioContextRef.current.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContextRef.current.destination);
            currentSourceRef.current = source; // Track for stop

            source.onended = () => {
                currentSourceRef.current = null;
                // Release mutex before processing next chunk
                isPlayingRef.current = false;
                playNextAudioChunk();
            };

            source.start();

        } catch (err) {
            console.error('Error playing audio:', err);
            currentSourceRef.current = null;
            // Ensure mutex is released on error
            isPlayingRef.current = false;
            // Try next chunk
            playNextAudioChunk();
        }
    };

    // Stop agent speech: clear queue, stop current audio, notify backend
    const stopAgentSpeech = useCallback(() => {
        console.log('Stopping agent speech');

        // 1. Clear the audio queue
        audioQueueRef.current = [];
        audioQueueRef.current._audioEndReceived = false;

        // 2. Stop currently playing audio source
        if (currentSourceRef.current) {
            try {
                currentSourceRef.current.onended = null; // Prevent callback
                currentSourceRef.current.stop();
            } catch (e) {
                // Already stopped
            }
            currentSourceRef.current = null;
        }

        // 3. Release playback mutex
        isPlayingRef.current = false;

        // 4. Update state - AI is no longer speaking
        setIsAISpeaking(false);
        isAISpeakingRef.current = false;

        // 5. Notify backend to cancel any ongoing TTS streaming
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'control',
                action: 'stop_speech'
            }));
        }
    }, []);

    // Toggle voice mode ON/OFF
    const toggleVoiceMode = useCallback(async () => {
        if (!voiceModeEnabled) {
            // Enter voice mode
            console.log('Entering voice mode');
            setVoiceModeEnabled(true);
            voiceModeEnabledRef.current = true;

            // Ensure voice WebSocket is connected before starting mic
            if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
                console.log('Voice WebSocket not open, reconnecting...');
                connect(languageRef.current);
            }

            // Start microphone streaming
            await startMicrophoneStream();
        } else {
            // Exit voice mode
            console.log('Exiting voice mode');
            setVoiceModeEnabled(false);
            voiceModeEnabledRef.current = false;
            setIsUserSpeaking(false);

            // Stop any playing audio
            stopAgentSpeech();

            // Stop microphone
            stopMicrophoneStream();
        }
    }, [voiceModeEnabled, stopAgentSpeech, connect]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            // Cancel any pending reconnect
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
            stopMicrophoneStream();
            if (socketRef.current) {
                // Remove onclose to prevent reconnect during cleanup
                socketRef.current.onclose = null;
                socketRef.current.close();
                socketRef.current = null;
            }
        };
    }, []);

    // Helper functions
    const convertFloat32ToInt16 = (float32) => {
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16;
    };

    const convertInt16ToFloat32 = (int16) => {
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
            float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF);
        }
        return float32;
    };

    const arrayBufferToBase64 = (buffer) => {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    };

    const base64ToArrayBuffer = (base64) => {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    };

    return {
        connect,
        toggleVoiceMode,
        stopAgentSpeech,
        voiceModeEnabled,
        isConnected,
        isRecording,
        isProcessing,
        isUserSpeaking,
        isAISpeaking,
        transcript,
        responseText,
        error
    };
}
