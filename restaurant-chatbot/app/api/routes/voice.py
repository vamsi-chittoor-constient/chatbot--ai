"""
Voice Chat WebSocket API
Real-time voice interaction with speech-to-text and text-to-speech

Supports multiple VAD engines via VAD_ENGINE environment variable:
- silero (default): Best multilingual support (6000+ languages)
- ten: Lower latency, better accuracy on short pauses
- webrtc: Lightweight, minimal resources
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import structlog
import asyncio
import base64
import io
import json
import os
import numpy as np
from openai import AsyncOpenAI

# Import VAD abstraction layer
from app.services.vad import get_vad, detect_speech, VAD_ENGINE

logger = structlog.get_logger(__name__)

router = APIRouter()

# OpenAI client for Whisper (STT) and TTS
async def get_openai_client():
    import os
    # Try to use dedicated voice API key first
    voice_api_key = os.getenv("OPENAI_VOICE_API_KEY")

    if voice_api_key:
        logger.debug("Using dedicated voice API key")
        return AsyncOpenAI(api_key=voice_api_key)

    # Fallback to regular API key rotation
    from app.ai_services.llm_manager import get_llm_manager
    llm_manager = get_llm_manager()
    api_key = llm_manager.get_next_api_key()
    return AsyncOpenAI(api_key=api_key)


@router.websocket("/ws/voice/{session_id}")
async def voice_chat_websocket(
    websocket: WebSocket,
    session_id: str,
    language: Optional[str] = Query(default="English")
):
    """
    Real-time voice chat WebSocket endpoint with Silero VAD.

    Protocol:
    - Client sends: {"type": "audio_chunk", "audio": "<base64 PCM16 data>"}
    - Server detects speech with Silero VAD
    - Server sends: {"type": "speech_started"} when speech detected
    - Server sends: {"type": "speech_ended"} when speech ends
    - Server sends: {"type": "transcript", "text": "..."}
    - Server sends: {"type": "audio_chunk", "audio": "<base64 PCM16 data>"}

    Flow:
    1. Client streams audio chunks continuously (PCM 16-bit, 16kHz for VAD)
    2. Server uses Silero VAD to detect speech boundaries
    3. Server transcribes speech segments with Whisper
    4. Server processes with chat agent
    5. Server synthesizes response with TTS
    6. Server streams audio back to client
    """
    await websocket.accept()

    logger.info(
        "voice_websocket_connected",
        session_id=session_id,
        language=language
    )

    # NOTE: Do NOT set voice_mode on connection!
    # Voice mode should only be active when user is actually speaking/using voice.
    # Setting it on connect steals ALL events from chat queue (SEARCH_RESULTS, MENU_DATA, etc.)
    # which breaks the chat UI cards.
    # Voice mode will be set when voice_start message is received.
    from app.core.agui_events import set_voice_mode
    # set_voice_mode(session_id, websocket)  # DISABLED - was breaking chat cards

    # Load VAD model (configurable via VAD_ENGINE env var)
    vad = get_vad()
    logger.info(f"Using VAD engine: {VAD_ENGINE}", session_id=session_id)

    # Audio buffer for VAD processing
    audio_buffer = []  # List of PCM chunks
    speech_buffer = []  # Buffer for detected speech
    is_speaking = False
    silence_frames = 0  # Counter for consecutive silent frames (hangover mechanism)
    # Mutable state container for sharing between main loop and background tasks
    state = {"is_processing": False}
    SAMPLE_RATE = 16000  # All VAD engines work at 16kHz
    VAD_CHUNK_SIZE = 512  # Chunk size (32ms at 16kHz)

    # VAD Sensitivity Settings (configurable via env vars)
    # SPEECH_THRESHOLD: Probability above which speech is detected (default 0.6)
    # SILENCE_THRESHOLD: Probability below which silence is detected (default 0.3)
    # SILENCE_FRAMES_REQUIRED: Consecutive silent frames needed to end speech (~500ms default)
    SPEECH_THRESHOLD = float(os.getenv("VAD_SPEECH_THRESHOLD", "0.6"))
    SILENCE_THRESHOLD = float(os.getenv("VAD_SILENCE_THRESHOLD", "0.3"))
    SILENCE_FRAMES_REQUIRED = int(os.getenv("VAD_SILENCE_FRAMES", "15"))

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "language": language
        })

        while True:
            try:
                # Receive audio chunk from client with timeout for keepalive
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_json({"type": "ping"})
                    continue

                message = json.loads(data)

                if message["type"] == "audio_chunk":
                    # Decode base64 audio (PCM 16-bit)
                    audio_data = base64.b64decode(message["audio"])
                    audio_buffer.append(audio_data)
                    # Note: Removed per-chunk logging to reduce log spam

                    # Convert to float32 for VAD (all engines use float32 input)
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    # Run VAD on chunk (uses configured engine)
                    speech_prob = vad.detect_speech(audio_float32, SAMPLE_RATE)

                    # Speech detection with hangover mechanism
                    # Prevents premature cutoff during brief pauses in speech
                    if speech_prob > SPEECH_THRESHOLD:
                        # Speech detected - reset silence counter
                        silence_frames = 0

                        if not is_speaking:
                            # Speech started
                            is_speaking = True
                            speech_buffer = []
                            await websocket.send_json({"type": "speech_started"})
                            logger.debug("Speech started", session_id=session_id, prob=speech_prob)

                        # Add to speech buffer
                        speech_buffer.append(audio_data)

                    elif speech_prob < SILENCE_THRESHOLD:
                        # Clear silence detected
                        if is_speaking:
                            # Still collecting speech, but counting silence frames
                            silence_frames += 1
                            speech_buffer.append(audio_data)  # Keep buffering during hangover

                            if silence_frames >= SILENCE_FRAMES_REQUIRED:
                                # Enough silence - speech truly ended
                                is_speaking = False
                                silence_frames = 0
                                await websocket.send_json({"type": "speech_ended"})
                                logger.debug("Speech ended (after hangover)", session_id=session_id)

                                # Process speech segment in background task
                                if speech_buffer and not state["is_processing"]:
                                    state["is_processing"] = True
                                    asyncio.create_task(
                                        process_speech_segment(
                                            websocket,
                                            speech_buffer.copy(),
                                            session_id,
                                            language,
                                            state
                                        )
                                    )
                                    speech_buffer = []
                                elif state["is_processing"]:
                                    logger.debug("Accumulating speech while processing", session_id=session_id)
                    else:
                        # Ambiguous zone (between SILENCE_THRESHOLD and SPEECH_THRESHOLD)
                        # Keep buffering if speaking, don't increment silence counter
                        if is_speaking:
                            speech_buffer.append(audio_data)

            except WebSocketDisconnect:
                logger.info("voice_websocket_disconnected", session_id=session_id)
                break
            except Exception as e:
                logger.error(
                    "voice_websocket_error",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True
                )
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except Exception as e:
        logger.error(
            "voice_websocket_fatal_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
    finally:
        # Clean up voice mode registration
        try:
            from app.core.agui_events import set_voice_mode
            set_voice_mode(session_id, None)  # Disable voice mode
        except:
            pass

        try:
            await websocket.close()
        except:
            pass


async def process_speech_segment(
    websocket: WebSocket,
    speech_buffer: list,
    session_id: str,
    language: str,
    state: dict = None
):
    """
    Process detected speech segment:
    1. Combine chunks
    2. Transcribe with Whisper
    3. Process with chat agent
    4. Synthesize response
    5. Stream back to client
    """
    try:
        # Combine audio chunks
        combined_audio = b''.join(speech_buffer)

        # Minimum 1 second of audio to reduce hallucinations (was 0.5s)
        # At 16kHz mono 16-bit: 16000 Hz * 1 sec * 2 bytes = 32000 bytes
        MIN_AUDIO_BYTES = 32000
        if len(combined_audio) < MIN_AUDIO_BYTES:
            logger.debug(
                "voice_segment_too_short",
                session_id=session_id,
                length=len(combined_audio),
                threshold=MIN_AUDIO_BYTES
            )
            # Reset state before returning
            if state is not None:
                state["is_processing"] = False
            return  # Too short, probably noise

        # Convert PCM to WAV format for Whisper (16kHz is fine for Whisper)
        wav_data = pcm_to_wav(combined_audio, sample_rate=16000)

        # Transcribe with Whisper
        await websocket.send_json({"type": "processing_start"})

        client = await get_openai_client()

        # Create temporary file-like object
        audio_file = io.BytesIO(wav_data)
        audio_file.name = "audio.wav"

        # Transcribe with Whisper
        # Note: Whisper works best with audio >= 0.5 seconds
        logger.debug(
            "voice_transcribing",
            session_id=session_id,
            audio_length=len(combined_audio),
            language=language
        )

        # Whisper transcription with language-specific vocabulary hints
        # Using vocabulary hint in the TARGET language improves accuracy
        # DO NOT use English hints for Hindi/Tamil - it causes hallucinations!

        # Language-specific vocabulary hints
        vocabulary_hints = {
            "English": (
                "dosa, idli, vada, sambar, chutney, masala dosa, parota, paratha, biryani, "
                "paneer, butter chicken, naan, roti, dal, tandoori, tikka, korma, vindaloo, "
                "lassi, chai, menu, cart, order, checkout, table, reservation, booking"
            ),
            "Hindi": (
                "दोसा, इडली, वड़ा, सांभर, चटनी, मसाला डोसा, पराठा, बिरयानी, "
                "पनीर, बटर चिकन, नान, रोटी, दाल, तंदूरी, टिक्का, कोरमा, "
                "लस्सी, चाय, मेनू, कार्ट, ऑर्डर, चेकआउट, टेबल, बुकिंग, "
                "खाना, पीना, दो, तीन, चार, एक, कितना, दीजिए, चाहिए"
            ),
            "Tamil": (
                "தோசை, இட்லி, வடை, சாம்பார், சட்னி, மசாலா தோசை, பரோட்டா, பிரியாணி, "
                "பன்னீர், நான், ரொட்டி, தால், தந்தூரி, டிக்கா, "
                "லஸ்ஸி, டீ, மெனு, கார்ட், ஆர்டர், செக்அவுட், டேபிள், புக்கிங், "
                "சாப்பாடு, இரண்டு, மூன்று, நான்கு, ஒன்று, எவ்வளவு, வேண்டும்"
            ),
        }

        # Get language-specific hint (or empty for unsupported languages)
        vocabulary_hint = vocabulary_hints.get(language, "")

        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language_code_map.get(language, "en"),
            prompt=vocabulary_hint if vocabulary_hint else None,  # Only use hint if available
            temperature=0.0,  # Lower temperature to reduce hallucinations
        )

        transcript_text = transcription.text.strip()

        # =========================================================================
        # HALLUCINATION FILTERING - Detect infinite loops / repetition
        # =========================================================================
        # Whisper sometimes hallucinates by repeating a phrase infinitely on silence
        # e.g., "Thank you. Thank you. Thank you." or "how many potatoes" x50

        from collections import Counter
        import re

        # Normalize text for analysis (remove punctuation, lowercase)
        normalized = re.sub(r'[^\w\s]', ' ', transcript_text.lower())
        words = normalized.split()

        if len(words) >= 6:
            # Check 1: Single word repetition (>40% same word = hallucination)
            word_counts = Counter(words)
            most_common_word = word_counts.most_common(1)
            if most_common_word and most_common_word[0][1] > len(words) * 0.4:
                logger.warning(
                    "voice_hallucination_word_repetition",
                    session_id=session_id,
                    word=most_common_word[0][0],
                    count=most_common_word[0][1],
                    total=len(words)
                )
                await websocket.send_json({"type": "processing_end"})
                if state is not None:
                    state["is_processing"] = False
                return

            # Check 2: N-gram repetition (2, 3, or 4 word phrases repeated 3+ times)
            for n in [2, 3, 4]:
                if len(words) >= n * 3:  # Need at least 3 repetitions
                    grams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
                    gram_counts = Counter(grams)
                    most_common_gram = gram_counts.most_common(1)
                    if most_common_gram and most_common_gram[0][1] >= 3:
                        logger.warning(
                            "voice_hallucination_ngram_repetition",
                            session_id=session_id,
                            phrase=most_common_gram[0][0],
                            count=most_common_gram[0][1],
                            n=n
                        )
                        await websocket.send_json({"type": "processing_end"})
                        if state is not None:
                            state["is_processing"] = False
                        return

            # Check 3: Very long transcripts are suspicious (>100 words from short audio)
            if len(words) > 100:
                logger.warning(
                    "voice_hallucination_too_long",
                    session_id=session_id,
                    word_count=len(words)
                )
                await websocket.send_json({"type": "processing_end"})
                if state is not None:
                    state["is_processing"] = False
                return

        # Filter out known garbage patterns (Whisper artifacts)
        garbage_patterns = [
            "This is a conversation with a restaurant",
            "Thank you for watching",
            "Thanks for watching",
            "Please subscribe",
            "Like and subscribe",
            "Notes:",
            "Transcribed by",
            "Amara.org"
        ]
        for pattern in garbage_patterns:
            if pattern.lower() in transcript_text.lower():
                logger.warning(
                    "voice_garbage_transcript_filtered",
                    session_id=session_id,
                    transcript=transcript_text
                )
                await websocket.send_json({"type": "processing_end"})
                if state is not None:
                    state["is_processing"] = False
                return

        if not transcript_text:
            await websocket.send_json({"type": "processing_end"})
            if state is not None:
                state["is_processing"] = False
            return

        logger.info(
            "voice_transcript",
            session_id=session_id,
            transcript=transcript_text
        )

        # Send transcript to client
        await websocket.send_json({
            "type": "transcript",
            "text": transcript_text
        })

        # Process with chat agent (with full AGUI support)
        response_text = await process_with_chat_agent(
            transcript_text,
            session_id,
            websocket,
            language=language
        )

        # Ensure response_text is a string
        if not isinstance(response_text, str):
            response_text = str(response_text)

        logger.info(
            "voice_response",
            session_id=session_id,
            response_preview=response_text[:100] if len(response_text) > 100 else response_text
        )

        # Send text response to client (for display while audio plays)
        await websocket.send_json({
            "type": "response_text",
            "text": response_text
        })

        # Synthesize speech with HD quality
        await websocket.send_json({"type": "audio_start"})

        # Stream TTS audio back to client using proper async streaming
        CHUNK_SIZE = 4096
        async with client.audio.speech.with_streaming_response.create(
            model="tts-1-hd",  # HD quality for clearer, more natural speech
            voice="nova",  # Female voice (alloy, echo, fable, onyx, nova, shimmer)
            input=response_text,
            response_format="pcm",  # Raw PCM for streaming
            speed=1.0  # Natural speed
        ) as tts_response:
            # Stream audio chunks to client
            async for chunk in tts_response.iter_bytes(chunk_size=CHUNK_SIZE):
                if chunk:
                    base64_chunk = base64.b64encode(chunk).decode('utf-8')
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "audio": base64_chunk
                    })

        await websocket.send_json({"type": "audio_end"})
        await websocket.send_json({"type": "processing_end"})

    except Exception as e:
        logger.error(
            "voice_processing_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        await websocket.send_json({
            "type": "error",
            "message": "Failed to process audio"
        })
        await websocket.send_json({"type": "processing_end"})
    finally:
        # Reset processing state to allow new requests
        if state is not None:
            state["is_processing"] = False
            logger.debug("Processing state reset", session_id=session_id)


async def process_with_chat_agent(text: str, session_id: str, websocket: WebSocket, language: str = "English") -> str:
    """
    Process user's text with the chat agent and return response.
    Voice mode supports full AGUI experience: forms, menus, cards, etc.

    Args:
        text: User's message (transcribed from voice)
        session_id: Session identifier
        websocket: Voice WebSocket for AGUI events
        language: Response language (English, Hindi, Tamil, etc.)
    """
    try:
        # Import chat processing
        from app.orchestration.restaurant_crew import process_with_agui_streaming
        from app.core.agui_events import AGUIEventEmitter, set_voice_mode, flush_pending_events, get_event_queue
        from app.services.session_manager import get_session_manager

        # Get session data
        session_manager = get_session_manager()
        session = await session_manager.get_session(session_id)

        if not session:
            if language == "Hindi":
                return "Maaf kijiye, aapka session nahi mila. Please refresh karke dubara try kijiye."
            elif language == "Tamil":
                return "Mannikkavum, ungal session kandupidikka mudiyavillai. Thayavu seidhu refresh seidhu meeNdum muayarchi seyyungal."
            return "I'm sorry, I couldn't find your session. Please refresh and try again."

        # Get conversation history from session metadata
        conversation_history = session.metadata.get("conversation_history", []) if session.metadata else []
        user_id = session.user_id

        # Add language instruction to the user message for the agent
        # This tells the agent to respond in the specified language (Hinglish style)
        if language == "Hindi":
            # Prepend language instruction - Hinglish style (Hindi with English food/menu terms)
            text = f"[RESPOND IN HINGLISH - Use Hindi language but keep food item names, menu terms, prices in English. Example: 'Aapka order mein 2 Masala Dosa add kar diya hai, total ₹250 ho gaya'] {text}"
        elif language == "Tamil":
            # Tamil with English terms
            text = f"[RESPOND IN TANGLISH - Use Tamil language but keep food item names, menu terms, prices in English. Example: 'Ungal order-la 2 Masala Dosa add panniten, total ₹250 aagum'] {text}"

        # Enable voice mode ONLY during processing (not on connect)
        # This routes tool events (SEARCH_RESULTS, MENU_DATA) to voice WebSocket
        set_voice_mode(session_id, websocket)

        # Create a real emitter that forwards ALL AGUI events through WebSocket
        # Voice mode needs full interactive experience: forms, menus, cards, etc.
        class VoiceWebSocketEmitter:
            def __init__(self, ws):
                self.ws = ws

            def emit_run_started(self):
                pass  # Optional

            def emit_activity(self, activity_type: str, message: str):
                asyncio.create_task(self.ws.send_json({
                    "type": "agui_event",
                    "agui": {
                        "type": "ACTIVITY_START",
                        "activity_type": activity_type,
                        "message": message
                    }
                }))

            def emit_activity_end(self):
                asyncio.create_task(self.ws.send_json({
                    "type": "agui_event",
                    "agui": {"type": "ACTIVITY_END"}
                }))

            def emit_full_text(self, text: str, chunk_size: int = 1):
                """Emit full text - for voice mode we don't stream, just pass through"""
                # Voice mode handles text differently (TTS), so we just store it
                pass  # Text is returned directly, not streamed via AGUI

            def emit_quick_replies(self, options):
                """Emit quick reply options"""
                asyncio.create_task(self.ws.send_json({
                    "type": "agui_event",
                    "agui": {
                        "type": "QUICK_REPLIES",
                        "options": options
                    }
                }))

            def emit_run_error(self, error: str):
                pass  # Errors handled separately

            def emit_run_finished(self, response: str = None):
                pass  # Optional - voice mode handles response via TTS

        emitter = VoiceWebSocketEmitter(websocket)

        try:
            # Process with agent
            response, _ = await process_with_agui_streaming(
                user_message=text,
                session_id=session_id,
                conversation_history=conversation_history,
                emitter=emitter,
                user_id=user_id
            )

            # Flush any remaining staged events to voice WebSocket
            # (events staged in thread pool before voice_mode was checked)
            flush_pending_events(session_id)

            # Also drain the queue and forward to voice WebSocket
            # (in case events were queued before voice_mode was set)
            queue = get_event_queue(session_id)
            while not queue.empty():
                try:
                    event = queue.get_nowait()
                    await websocket.send_json({
                        "type": "agui_event",
                        "agui": event.to_dict() if hasattr(event, 'to_dict') else {"type": event.type.value, **event.__dict__}
                    })
                except:
                    break

        finally:
            # CRITICAL: Disable voice mode after processing
            # This ensures chat mode gets events when not in voice processing
            set_voice_mode(session_id, None)

        # Update conversation history
        conversation_history.append(f"User: {text}")
        conversation_history.append(f"Assistant: {response}")

        # Keep last 10 messages
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]

        # Update session metadata with conversation history
        updated_metadata = session.metadata.copy() if session.metadata else {}
        updated_metadata["conversation_history"] = conversation_history
        await session_manager.update_session(
            session_id,
            metadata=updated_metadata
        )

        return response

    except Exception as e:
        logger.error(
            "chat_agent_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        # Return localized error message
        if language == "Hindi":
            return "Maaf kijiye, kuch तकनीकी (technical) dikkat aa gayi. Please dobara boliye."
        elif language == "Tamil":
            return "Mannikkavum, oru technical problem erpattullathu. Thayavu seidhu meeNdum sollungal."
        
        return "I'm sorry, I encountered an error processing your request. Please try again."


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """
    Convert raw PCM data to WAV format.
    """
    import struct

    # WAV header
    num_samples = len(pcm_data) // (bits_per_sample // 8)
    datasize = num_samples * channels * (bits_per_sample // 8)

    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + datasize,
        b'WAVE',
        b'fmt ',
        16,  # fmt chunk size
        1,   # PCM format
        channels,
        sample_rate,
        sample_rate * channels * (bits_per_sample // 8),  # byte rate
        channels * (bits_per_sample // 8),  # block align
        bits_per_sample,
        b'data',
        datasize
    )

    return wav_header + pcm_data


# Language code mapping for Whisper
language_code_map = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Malayalam": "ml",
    "Kannada": "kn",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
}
