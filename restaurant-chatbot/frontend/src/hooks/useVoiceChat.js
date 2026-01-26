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

    const connect = useCallback((language = 'English') => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
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
                setIsRecording(false);
                stopMicrophoneStream();
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
                setIsAISpeaking(false);
                // In continuous voice mode, microphone keeps running
                // No need to restart anything
                break;

            case 'agui_event':
                // Forward AG-UI events (menu cards, cart, search results, quick replies, etc.)
                // to the same handler used by chat mode so cards render in the UI
                if (data.agui && onEvent) {
                    console.log('Voice AGUI event:', data.agui.type || data.agui);
                    onEvent(data.agui);
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

            source.onended = () => {
                // Release mutex before processing next chunk
                isPlayingRef.current = false;
                playNextAudioChunk();
            };

            source.start();

        } catch (err) {
            console.error('Error playing audio:', err);
            // Ensure mutex is released on error
            isPlayingRef.current = false;
            // Try next chunk
            playNextAudioChunk();
        }
    };

    // Toggle voice mode ON/OFF
    const toggleVoiceMode = useCallback(async () => {
        if (!voiceModeEnabled) {
            // Enter voice mode
            console.log('Entering voice mode');
            setVoiceModeEnabled(true);
            voiceModeEnabledRef.current = true;

            // Start microphone streaming
            await startMicrophoneStream();
        } else {
            // Exit voice mode
            console.log('Exiting voice mode');
            setVoiceModeEnabled(false);
            voiceModeEnabledRef.current = false;
            setIsUserSpeaking(false);

            // Stop microphone
            stopMicrophoneStream();
        }
    }, [voiceModeEnabled]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopMicrophoneStream();
            if (socketRef.current) {
                socketRef.current.close();
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
