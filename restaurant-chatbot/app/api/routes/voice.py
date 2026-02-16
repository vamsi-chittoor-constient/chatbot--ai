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
import collections
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

    # Use longer timeout for voice operations (transcription can be slow on poor networks)
    from httpx import Timeout
    voice_timeout = Timeout(60.0, connect=30.0)  # 60s total, 30s to connect

    if voice_api_key:
        logger.debug("Using dedicated voice API key")
        return AsyncOpenAI(api_key=voice_api_key, timeout=voice_timeout)

    # Fallback to regular API key rotation
    from app.ai_services.llm_manager import get_llm_manager
    llm_manager = get_llm_manager()
    api_key = llm_manager.get_next_api_key()
    return AsyncOpenAI(api_key=api_key, timeout=voice_timeout)


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
    # Pre-buffer: rolling window of recent chunks (10 × 32ms = 320ms lookback)
    # Captures soft speech onsets (e.g., "I" in "I like") that fall below
    # SPEECH_THRESHOLD and would otherwise be clipped by the VAD.
    pre_buffer = collections.deque(maxlen=10)
    is_speaking = False
    silence_frames = 0  # Counter for consecutive silent frames (hangover mechanism)
    # Mutable state container for sharing between main loop and background tasks
    # stop_requested: set by client control message to cancel TTS mid-stream
    # consecutive_hallucinations: prevents TTS echo feedback loops
    state = {"is_processing": False, "stop_requested": False, "consecutive_hallucinations": 0}
    SAMPLE_RATE = 16000  # All VAD engines work at 16kHz
    VAD_CHUNK_SIZE = 512  # Chunk size (32ms at 16kHz)

    # VAD Sensitivity Settings (configurable via env vars)
    # SPEECH_THRESHOLD: Probability above which speech is detected (default 0.6)
    # SILENCE_THRESHOLD: Probability below which silence is detected (default 0.3)
    # SILENCE_FRAMES_REQUIRED: 60 frames × 32ms = ~2 seconds of silence before processing
    SPEECH_THRESHOLD = float(os.getenv("VAD_SPEECH_THRESHOLD", "0.6"))
    SILENCE_THRESHOLD = float(os.getenv("VAD_SILENCE_THRESHOLD", "0.3"))
    SILENCE_FRAMES_REQUIRED = int(os.getenv("VAD_SILENCE_FRAMES", "60"))

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

                if message.get("type") == "control":
                    action = message.get("action", "")
                    if action == "stop_speech":
                        # Client requested to stop AI speech (user clicked Stop button)
                        state["stop_requested"] = True
                        logger.info("voice_stop_requested", session_id=session_id)
                    continue

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
                            # Speech started — seed with pre-buffer to recover
                            # soft onsets (e.g. "I" in "I like to take away")
                            is_speaking = True
                            speech_buffer = list(pre_buffer)
                            await websocket.send_json({"type": "speech_started"})
                            logger.info("voice_speech_started", session_id=session_id, language=language, pre_buffer_chunks=len(speech_buffer))

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
                                logger.info("voice_speech_ended", session_id=session_id, buffer_chunks=len(speech_buffer))

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

                    # Update pre-buffer AFTER VAD decision so it contains prior
                    # chunks (not the current one) when speech onset is detected.
                    pre_buffer.append(audio_data)

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


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """Send JSON to WebSocket, returning False if connection is closed."""
    try:
        await websocket.send_json(data)
        return True
    except RuntimeError:
        # WebSocket already closed (e.g. client disconnected during processing)
        return False


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

        # Minimum 0.5 second of audio to allow short confirmations ("yes", "no", "okay")
        # At 16kHz mono 16-bit: 16000 Hz * 0.5 sec * 2 bytes = 16000 bytes
        MIN_AUDIO_BYTES = 16000
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

        # ----- Audio preprocessing pipeline -----
        # 1. Spectral noise reduction  2. Silence trimming  3. Normalization
        import noisereduce as nr

        samples = np.frombuffer(combined_audio, dtype=np.int16).astype(np.float32)

        # Step 1: Spectral noise reduction — remove stationary background noise
        # (fan, AC, laptop hum) while preserving speech frequencies
        cleaned = nr.reduce_noise(
            y=samples,
            sr=16000,
            stationary=True,
            prop_decrease=0.75,
        )

        # Step 2: Silence trimming — strip leading/trailing silence
        # Prevents Whisper hallucinations on quiet sections at start/end
        silence_threshold = 500  # amplitude threshold for "silence"
        abs_signal = np.abs(cleaned)
        voiced = np.where(abs_signal > silence_threshold)[0]
        if len(voiced) > 0:
            # Keep a small margin (800 samples = 50ms) around speech
            margin = 800
            start = max(0, voiced[0] - margin)
            end = min(len(cleaned), voiced[-1] + margin)
            cleaned = cleaned[start:end]
        else:
            # All silence after denoising — skip
            logger.debug("voice_segment_all_silence_after_denoise", session_id=session_id)
            if state is not None:
                state["is_processing"] = False
            return

        # Skip if trimmed audio is too short (< 0.25s at 16kHz)
        # Allows short confirmations while filtering very brief noise
        if len(cleaned) < 4000:
            logger.debug("voice_segment_too_short_after_trim", session_id=session_id, samples=len(cleaned))
            if state is not None:
                state["is_processing"] = False
            return

        # Step 3: Normalize to consistent volume for Whisper
        peak = np.max(np.abs(cleaned))
        if peak > 0:
            cleaned = cleaned * (32000.0 / peak)

        preprocessed_audio = cleaned.astype(np.int16).tobytes()

        # Convert PCM to WAV format for Whisper (16kHz is fine for Whisper)
        wav_data = pcm_to_wav(preprocessed_audio, sample_rate=16000)

        # Transcribe with Whisper
        await websocket.send_json({"type": "processing_start"})

        client = await get_openai_client()

        # Create temporary file-like object
        audio_file = io.BytesIO(wav_data)
        audio_file.name = "audio.wav"

        # Transcribe with Whisper
        # Note: Whisper works best with audio >= 0.5 seconds
        logger.info(
            "voice_transcribing",
            session_id=session_id,
            audio_bytes=len(combined_audio),
            language=language
        )

        # Whisper vocabulary hints — ONLY food/brand names Whisper wouldn't know.
        # Do NOT include phrases or sentences — Whisper echoes them as hallucinations
        # when it can't understand the audio well (e.g. Tamil speech with language="en").
        vocabulary_hints = {
            "English": (
                "Aswins, amla, nannari, badam gheer, badam kulfi, jigardhanda, "
                "ilaneer payasam, dosai, parota, appalam, beeda, podi"
            ),
            "Hindi": (
                "Masala Dosa, Rava Dosa, Ghee Dosa, Paneer Biryani, Idli, Vada, "
                "Sambar, Appalam, Beeda, Parota, Dosai, Cold Coffee, Apple Juice, "
                "Cheese Slice, Chicken Fillet, Badam Kulfi, Jigardhanda, "
                "Nugget Sauce, French Fries, Fries, Garlic Sauce, Cocktail Sauce"
            ),
            "Tamil": (
                "Masala Dosa, Rava Dosa, Ghee Dosa, Paneer Biryani, Idli, Vada, "
                "Sambar, Appalam, Beeda, Parota, Dosai, Cold Coffee, Apple Juice, "
                "Cheese Slice, Chicken Fillet, Badam Kulfi, Jigardhanda, "
                "Nugget Sauce, French Fries, Fries, Garlic Sauce, Cocktail Sauce"
            ),
        }

        # Get language-specific prompt
        vocabulary_hint = vocabulary_hints.get(language, "")

        # Always use language="en" so Whisper outputs English letters.
        # For code-switched speech (Tanglish/Hinglish) this transcribes
        # exactly what the user said in English phonetics.
        whisper_kwargs = {
            "model": "whisper-1",
            "file": audio_file,
            "prompt": vocabulary_hint if vocabulary_hint else None,
            "temperature": 0.0,
            "response_format": "verbose_json",
            "language": "en",
        }

        transcription = await client.audio.transcriptions.create(**whisper_kwargs)

        # Validate transcription quality using confidence scores
        if hasattr(transcription, 'avg_logprob'):
            if transcription.avg_logprob < -0.8:
                logger.warning(
                    "Low confidence transcription detected",
                    session_id=session_id,
                    language=language,
                    avg_logprob=transcription.avg_logprob,
                    text_preview=transcription.text[:50] if len(transcription.text) > 50 else transcription.text
                )

        transcript_text = transcription.text.strip()

        # =========================================================================
        # HALLUCINATION FILTERING - Detect prompt leaks + infinite loops
        # On hallucination: ask user to repeat instead of silently dropping.
        # =========================================================================

        from collections import Counter
        import re

        _is_hallucination = False
        _hallucination_reason = ""

        # Check 0: Whisper prompt leak — on silence/noise Whisper sometimes
        # echoes the vocabulary hint or meta-words as the transcription.
        _prompt_fragments = [
            "transcribe exactly as spoken",
            "keeping english words unchanged",
            "roman script",
            "common hinglish phrases",
            "common tanglish phrases",
            "this conversation mixes",
        ]
        _text_lower = transcript_text.lower().strip()

        # Single-word or very short prompt leaks (meta labels, not real speech)
        _meta_words = {"tanglish", "hinglish", "tamil", "hindi", "english", "transcript", "transcription"}
        if _text_lower in _meta_words:
            _is_hallucination = True
            _hallucination_reason = f"meta_word: {transcript_text}"

        if not _is_hallucination and any(frag in _text_lower for frag in _prompt_fragments):
            _is_hallucination = True
            _hallucination_reason = f"prompt_leak: {transcript_text[:80]}"

        # Check 0b: Vocabulary hint echo — Whisper echoes the food-name hints
        # when it can't understand the audio. Detect if transcript closely
        # matches the vocabulary hint string (>60% word overlap).
        # SKIP for Hindi/Tamil: bilingual hints contain common conversational words
        # (मेनू, दिखाओ, checkout) that legitimately appear in real user speech.
        if not _is_hallucination and language == "English":
            _vocab_hint = vocabulary_hints.get(language, "").lower()
            if _vocab_hint and len(_text_lower.split()) >= 3:
                _hint_words = set(re.sub(r'[^\w\s]', ' ', _vocab_hint).split())
                _transcript_words = set(re.sub(r'[^\w\s]', ' ', _text_lower).split())
                if _transcript_words and _hint_words:
                    _overlap = len(_transcript_words & _hint_words) / len(_transcript_words)
                    if _overlap > 0.6:
                        _is_hallucination = True
                        _hallucination_reason = f"vocab_hint_echo: overlap={_overlap:.0%}"

        # Normalize text for analysis (remove punctuation, lowercase)
        normalized = re.sub(r'[^\w\s]', ' ', transcript_text.lower())
        words = normalized.split()

        if not _is_hallucination and len(words) >= 6:
            # Check 1: Single word repetition (>40% same word = hallucination)
            word_counts = Counter(words)
            most_common_word = word_counts.most_common(1)
            if most_common_word and most_common_word[0][1] > len(words) * 0.4:
                _is_hallucination = True
                _hallucination_reason = f"word_repetition: {most_common_word[0][0]} x{most_common_word[0][1]}"

            # Check 2: N-gram repetition (2, 3, or 4 word phrases repeated 3+ times)
            if not _is_hallucination:
                for n in [2, 3, 4]:
                    if len(words) >= n * 3:
                        grams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
                        gram_counts = Counter(grams)
                        most_common_gram = gram_counts.most_common(1)
                        if most_common_gram and most_common_gram[0][1] >= 3:
                            _is_hallucination = True
                            _hallucination_reason = f"ngram_repetition: '{most_common_gram[0][0]}' x{most_common_gram[0][1]}"
                            break

            # Check 3: Very long transcripts are suspicious (>100 words from short audio)
            if not _is_hallucination and len(words) > 100:
                _is_hallucination = True
                _hallucination_reason = f"too_long: {len(words)} words"

        # Filter out known garbage patterns (Whisper artifacts)
        if not _is_hallucination:
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
                    _is_hallucination = True
                    _hallucination_reason = f"garbage_pattern: {pattern}"
                    break

        # Handle hallucination: ask user to repeat (with feedback-loop prevention)
        if _is_hallucination:
            if state is not None:
                state["consecutive_hallucinations"] = state.get("consecutive_hallucinations", 0) + 1
            _consec = state.get("consecutive_hallucinations", 1) if state else 1

            logger.warning(
                "voice_hallucination_detected",
                session_id=session_id,
                reason=_hallucination_reason,
                transcript=transcript_text[:100],
                consecutive=_consec
            )

            # After 3+ consecutive hallucinations, silently drop to break the loop.
            # The VAD is likely picking up echo/ambient noise, not real speech.
            if _consec >= 3:
                logger.info("voice_hallucination_suppressed", session_id=session_id, consecutive=_consec)
                await _safe_send(websocket, {"type": "processing_end"})
                if state is not None:
                    state["is_processing"] = False
                return

            # First hallucination: send text + TTS so user knows to repeat.
            # Second+: send text only (NO TTS) to avoid echo feedback loop.
            _repeat_msg = "I'm sorry, I didn't catch that clearly. Could you please repeat?"
            await _safe_send(websocket, {"type": "response_text", "text": _repeat_msg})

            if _consec <= 1:
                # Only TTS on the FIRST hallucination; subsequent ones are text-only
                try:
                    client = await get_openai_client()
                    await _safe_send(websocket, {"type": "audio_start"})
                    async with client.audio.speech.with_streaming_response.create(
                        model="tts-1", voice="nova", input=_repeat_msg,
                        response_format="pcm", speed=1.0
                    ) as tts_response:
                        async for chunk in tts_response.iter_bytes(chunk_size=4096):
                            if chunk:
                                await _safe_send(websocket, {
                                    "type": "audio_chunk",
                                    "audio": base64.b64encode(chunk).decode('utf-8')
                                })
                    await _safe_send(websocket, {"type": "audio_end"})
                except Exception as _tts_err:
                    logger.debug("hallucination_tts_failed", error=str(_tts_err))

            await _safe_send(websocket, {"type": "processing_end"})
            if state is not None:
                state["is_processing"] = False
            return

        if not transcript_text:
            await websocket.send_json({"type": "processing_end"})
            if state is not None:
                state["is_processing"] = False
            return

        # Valid transcript — reset consecutive hallucination counter
        if state is not None:
            state["consecutive_hallucinations"] = 0

        logger.info(
            "voice_transcript",
            session_id=session_id,
            transcript=transcript_text
        )

        # Normalize transcript to clean English for non-English voice.
        # Whisper with language="en" is inconsistent on Hindi/Tamil speech —
        # sometimes outputs English translation, sometimes Romanized Hinglish,
        # sometimes completely wrong words ("Sambar" for a checkout request).
        # One GPT-4o-mini call makes it consistently English for both UI and crew.
        if language != "English" and language in ["Hindi", "Tamil"]:
            try:
                _norm_resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Translate to English. Keep food names, numbers, prices unchanged. Output ONLY the translation."},
                        {"role": "user", "content": transcript_text}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                normalized = _norm_resp.choices[0].message.content.strip()
                logger.info("voice_transcript_normalized", original=transcript_text, english=normalized)
                transcript_text = normalized
            except Exception as e:
                logger.warning("voice_transcript_normalize_failed", error=str(e))

        # Send transcript to client (clean English for display)
        await websocket.send_json({
            "type": "transcript",
            "text": transcript_text
        })

        # Process with chat agent (same clean English text)
        response_text, deferred_quick_replies = await process_with_chat_agent(
            transcript_text,
            session_id,
            websocket,
            language=language
        )

        # Ensure response_text is a string
        if not isinstance(response_text, str):
            response_text = str(response_text)

        # Strip internal tool context markers (e.g. [SEARCH RESULTS DISPLAYED ...])
        # These are meant for the LLM agent, not for user display/TTS.
        import re as _re
        response_text = _re.sub(
            r'\[(?:SEARCH RESULTS DISPLAYED|MENU CARD DISPLAYED|MENU DISPLAYED|CART CARD DISPLAYED'
            r'|EMPTY CART|ALTERNATIVE CATEGORY MENU DISPLAYED|INVALID QUANTITY|INVALID INSTRUCTIONS'
            r'|CHECKOUT COMPLETE|PAYMENT CONFIRMED|PAYMENT LINK SENT)'
            r'[^\]]*\]\s*',
            '', response_text
        ).strip()

        # Strip leaked language directive prefixes
        response_text = _re.sub(
            r'\[RESPOND IN (?:HINGLISH|TANGLISH)[^\]]*\]\s*',
            '', response_text, flags=_re.IGNORECASE
        ).strip()

        # Sanitize to catch any remaining prompt leaks, JSON, errors
        from app.core.response_sanitizer import sanitize_response as _sanitize
        response_text = _sanitize(response_text)

        logger.info(
            "voice_response",
            session_id=session_id,
            response_preview=response_text[:100] if len(response_text) > 100 else response_text
        )

        # Translate to target language (agent responds in English)
        display_text = await translate_for_tts(response_text, language, client)
        if display_text != response_text:
            logger.info(
                "voice_translation_applied",
                session_id=session_id,
                language=language,
                original_preview=response_text[:50] if len(response_text) > 50 else response_text,
                translated_preview=display_text[:50] if len(display_text) > 50 else display_text
            )

        # Send translated text response to client (for display)
        await websocket.send_json({
            "type": "response_text",
            "text": display_text
        })

        # Clear stop flag before starting TTS (fresh for this response)
        state["stop_requested"] = False

        # Stream TTS audio sentence-by-sentence for real-time playback
        logger.info("voice_tts_started", session_id=session_id, text_length=len(display_text), language=language)
        await websocket.send_json({"type": "audio_start"})

        # Split into sentences for faster streaming (audio starts before full text is processed)
        sentences = split_into_sentences(display_text)
        CHUNK_SIZE = 4096
        _tts_stopped = False

        for sentence in sentences:
            if not sentence.strip():
                continue

            # Check if client requested stop before starting next sentence
            if state.get("stop_requested"):
                logger.info("voice_tts_stopped_by_user", session_id=session_id)
                _tts_stopped = True
                break

            # Stream TTS for each sentence immediately
            async with client.audio.speech.with_streaming_response.create(
                model="tts-1",  # Use faster model for real-time streaming
                voice="nova",
                input=sentence,
                response_format="pcm",
                speed=1.0
            ) as tts_response:
                async for chunk in tts_response.iter_bytes(chunk_size=CHUNK_SIZE):
                    # Check stop flag between chunks
                    if state.get("stop_requested"):
                        logger.info("voice_tts_stopped_mid_sentence", session_id=session_id)
                        _tts_stopped = True
                        break
                    if chunk:
                        base64_chunk = base64.b64encode(chunk).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "audio": base64_chunk
                        })
            if _tts_stopped:
                break

        await websocket.send_json({"type": "audio_end"})
        state["stop_requested"] = False  # Reset for next interaction
        logger.info("voice_tts_complete", session_id=session_id, stopped=_tts_stopped)

        # Send deferred quick replies AFTER response_text and audio are done.
        # This ensures they arrive after TEXT_MESSAGE_START has cleared stale ones.
        if deferred_quick_replies:
            # Small delay to ensure React useEffect for responseText has fired
            await asyncio.sleep(0.15)
            for qr_options in deferred_quick_replies:
                await websocket.send_json({
                    "type": "agui_event",
                    "agui": {
                        "type": "QUICK_REPLIES",
                        "options": qr_options
                    }
                })
            logger.info(
                "voice_deferred_quick_replies_sent",
                session_id=session_id,
                count=len(deferred_quick_replies)
            )

        await _safe_send(websocket, {"type": "processing_end"})

    except RuntimeError as e:
        # WebSocket closed during processing (client navigated away, toggled voice off, etc.)
        logger.info("voice_ws_closed_during_processing", session_id=session_id, error=str(e))
    except Exception as e:
        logger.error(
            "voice_processing_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        await _safe_send(websocket, {"type": "error", "message": "Failed to process audio"})
        await _safe_send(websocket, {"type": "processing_end"})
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
                return "Maaf kijiye, aapka session nahi mila. Please refresh karke dubara try kijiye.", []
            elif language == "Tamil":
                return "Mannikkavum, ungal session kandupidikka mudiyavillai. Thayavu seidhu refresh seidhu meeNdum muayarchi seyyungal.", []
            return "I'm sorry, I couldn't find your session. Please refresh and try again.", []

        # Get conversation history from session metadata
        conversation_history = session.metadata.get("conversation_history", []) if session.metadata else []
        user_id = session.user_id

        # NOTE: Agent always responds in English. Translation to Hindi/Tamil happens
        # AFTER agent response, before TTS (see translate_for_tts below)

        # NOTE: We do NOT set voice_mode here. The voice_mode direct-send path
        # (_emit_to_voice_websocket_sync) fails silently from thread pool workers because
        # asyncio.get_event_loop() doesn't return the main loop. Instead, we let ALL
        # events go to the queue and drain them via the background task below.
        # set_voice_mode(session_id, websocket)  # DISABLED - use queue + background task instead

        # Deferred quick replies - sent AFTER response_text so they appear after
        # the AI response in the chat UI (TEXT_MESSAGE_START clears old quick_replies)
        deferred_quick_replies = []

        # Create a real emitter that forwards ALL AGUI events through WebSocket
        # Voice mode needs full interactive experience: forms, menus, cards, etc.
        class VoiceWebSocketEmitter:
            def __init__(self, ws):
                self.ws = ws

            def emit_run_started(self):
                from app.core.agui_events import _RUN_FINISHED_SESSIONS
                _RUN_FINISHED_SESSIONS.discard(session_id)
                asyncio.create_task(_safe_send(self.ws, {
                    "type": "agui_event",
                    "agui": {"type": "RUN_STARTED"}
                }))

            def emit_activity(self, activity_type: str, message: str):
                from app.core.agui_events import _RUN_FINISHED_SESSIONS
                if session_id in _RUN_FINISHED_SESSIONS:
                    return  # Gate closed, drop event
                asyncio.create_task(_safe_send(self.ws, {
                    "type": "agui_event",
                    "agui": {
                        "type": "ACTIVITY_START",
                        "activity_type": activity_type,
                        "message": message
                    }
                }))

            def emit_activity_end(self):
                asyncio.create_task(_safe_send(self.ws, {
                    "type": "agui_event",
                    "agui": {"type": "ACTIVITY_END"}
                }))

            def emit_full_text(self, text: str, chunk_size: int = 1):
                """Emit full text - for voice mode we don't stream, just pass through"""
                # Voice mode handles text differently (TTS), so we just store it
                pass  # Text is returned directly, not streamed via AGUI

            def emit_quick_replies(self, options):
                """Defer quick replies until after response_text is sent"""
                deferred_quick_replies.append(options)

            def emit_run_error(self, error: str):
                pass  # Errors handled separately

            def emit_run_finished(self, response: str = None):
                from app.core.agui_events import _RUN_FINISHED_SESSIONS
                _RUN_FINISHED_SESSIONS.add(session_id)
                asyncio.create_task(_safe_send(self.ws, {
                    "type": "agui_event",
                    "agui": {"type": "RUN_FINISHED"}
                }))

        emitter = VoiceWebSocketEmitter(websocket)

        # Start background task to stream AG-UI events from queue to voice WebSocket.
        # Tools emit events (MENU_DATA, SEARCH_RESULTS, CART_DATA) from sync thread pool
        # contexts where asyncio.get_event_loop() doesn't get the main loop, so the
        # direct voice_mode routing may fail silently. This background task catches any
        # events that end up in the queue instead.
        import json as _json

        async def _stream_agui_events_to_voice_ws():
            from app.core.agui_events import _RUN_FINISHED_SESSIONS
            queue = get_event_queue(session_id)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=0.5)
                        event_json = event.to_json() if hasattr(event, 'to_json') else _json.dumps({"type": getattr(event, 'type', 'UNKNOWN')})
                        event_data = _json.loads(event_json)
                        # Drop late ACTIVITY_START events after RUN_FINISHED
                        # (RUN_FINISHED is sent directly via WebSocket, but queued
                        # tool events arrive later — this filters the stale ones)
                        if event_data.get("type") == "ACTIVITY_START" and session_id in _RUN_FINISHED_SESSIONS:
                            continue
                        # Defer QUICK_REPLIES so they arrive after response_text
                        if event_data.get("type") == "QUICK_REPLIES":
                            # QuickRepliesEvent serializes as "replies", not "options"
                            opts = event_data.get("replies") or event_data.get("options") or []
                            if opts:  # Skip empty arrays to prevent overwriting valid ones
                                deferred_quick_replies.append(opts)
                            continue
                        await websocket.send_json({
                            "type": "agui_event",
                            "agui": event_data
                        })
                    except asyncio.TimeoutError:
                        continue
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.debug("voice_agui_stream_error", error=str(e))
                        continue
            except asyncio.CancelledError:
                pass

        agui_stream_task = asyncio.create_task(_stream_agui_events_to_voice_ws())

        try:
            # =================================================================
            # ALL MESSAGES GO TO AI AGENT - No interceptors
            # Checkout and payment handled by AI via tools:
            # checkout, select_payment_method, initiate_payment, cancel_payment
            # =================================================================

            # Process with agent
            # Pass real language so crew's INPUT translation fires (romanized
            # Tanglish/Hinglish → English for tool calls). voice_mode=True
            # skips crew's response translation — translate_for_tts handles it.
            response, _ = await process_with_agui_streaming(
                user_message=text,
                session_id=session_id,
                conversation_history=conversation_history,
                emitter=emitter,
                user_id=user_id,
                language=language,
                voice_mode=True
            )

            # Flush any remaining staged events to voice WebSocket
            # (events staged in thread pool before voice_mode was checked)
            flush_pending_events(session_id)

            # Give the background task a moment to process any remaining queued events
            await asyncio.sleep(0.3)

        finally:
            # Stop the background event streaming task
            agui_stream_task.cancel()
            try:
                await agui_stream_task
            except asyncio.CancelledError:
                pass

            # Drain any remaining events in the queue
            from app.core.agui_events import _RUN_FINISHED_SESSIONS
            queue = get_event_queue(session_id)
            while not queue.empty():
                try:
                    event = queue.get_nowait()
                    event_json = event.to_json() if hasattr(event, 'to_json') else _json.dumps({"type": getattr(event, 'type', 'UNKNOWN')})
                    event_data = _json.loads(event_json)
                    # Drop late ACTIVITY_START events after RUN_FINISHED
                    if event_data.get("type") == "ACTIVITY_START" and session_id in _RUN_FINISHED_SESSIONS:
                        continue
                    # Defer QUICK_REPLIES so they arrive after response_text
                    if event_data.get("type") == "QUICK_REPLIES":
                        # QuickRepliesEvent serializes as "replies", not "options"
                        opts = event_data.get("replies") or event_data.get("options") or []
                        if opts:  # Skip empty arrays to prevent overwriting valid ones
                            deferred_quick_replies.append(opts)
                        continue
                    await websocket.send_json({
                        "type": "agui_event",
                        "agui": event_data
                    })
                except:
                    break

            # Voice mode is not set (uses queue-based approach), so no cleanup needed

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

        return response, deferred_quick_replies

    except Exception as e:
        logger.error(
            "chat_agent_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        # Return localized error message
        if language == "Hindi":
            return "Maaf kijiye, kuch technical dikkat aa gayi. Please dobara boliye.", []
        elif language == "Tamil":
            return "Mannikkavum, oru technical problem erpattullathu. Thayavu seidhu meeNdum sollungal.", []

        return "I'm sorry, I encountered an error processing your request. Please try again.", []


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


def split_into_sentences(text: str) -> list:
    """
    Split text into sentences for real-time TTS streaming.
    Handles multiple languages including Hindi and Tamil.
    """
    import re

    # Split on sentence-ending punctuation (., !, ?, |, ।, ॥)
    # Include Hindi/Tamil sentence enders: । (Devanagari danda), ॥ (double danda)
    # Also split on | which is sometimes used as a pause marker
    sentences = re.split(r'(?<=[.!?।॥|])\s+', text)

    # Filter empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    # If no sentence breaks found, return the whole text
    if not sentences:
        return [text]

    return sentences


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


async def translate_for_tts(text: str, target_language: str, client: AsyncOpenAI) -> str:
    """
    Translate English text to target language for TTS output.
    Uses Hinglish/Tanglish style (native script mixed with English for food terms).

    Args:
        text: English text from agent
        target_language: Target language (Hindi, Tamil, etc.)
        client: OpenAI client for translation

    Returns:
        Translated text for TTS, or original if translation fails/not needed
    """
    # Only translate for non-English languages
    if target_language == "English" or target_language not in ["Hindi", "Tamil"]:
        return text

    try:
        # Language-specific translation prompts
        if target_language == "Hindi":
            system_prompt = """Translate to Hindi-English mix for TTS (text-to-speech) audio output. Rules:
- Write Hindi words in DEVANAGARI script (आपके, में, हो गये) — TTS pronounces native script correctly
- Keep English words in ENGLISH script: food names, "cart", "order", "add", "checkout", numbers, prices (₹)
- Mix both scripts naturally: "आपके cart में 2 Masala Dosa add हो गये, total ₹250"
- Use casual conversational Hindi — NOT formal/literary
- Keep it SHORT — this will be spoken aloud
- Output ONLY the translation

Example:
English: "I found 3 items matching your search. Would you like to add Masala Dosa to your cart?"
TTS: "आपकी search में 3 items मिले। Masala Dosa cart में add करना चाहते हो?"  """
        elif target_language == "Tamil":
            system_prompt = """Translate to Tamil-English mix for TTS (text-to-speech) audio output. Rules:
- Write Tamil words in TAMIL script (உங்க, இருக்கு, பண்ணுங்க) — TTS pronounces native script correctly
- Keep English words in ENGLISH script: food names, "cart", "order", "add", "checkout", numbers, prices (₹)
- Mix both scripts naturally: "உங்க cart ல 2 Masala Dosa add ஆயிடுச்சு, total ₹250"
- Use casual conversational Tamil — NOT formal/literary
- Keep it SHORT — this will be spoken aloud
- Output ONLY the translation

Example:
English: "I found 3 items matching your search. Would you like to add Masala Dosa to your cart?"
TTS: "உங்க search ல 3 items கிடைச்சுச்சு. Masala Dosa cart ல add பண்ணுமா?"  """
        else:
            return text

        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for translation
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,  # Low temperature for consistent translations
            max_tokens=500
        )

        translated = response.choices[0].message.content.strip()
        logger.debug(
            "voice_translation_complete",
            original_length=len(text),
            translated_length=len(translated),
            target_language=target_language
        )
        return translated

    except Exception as e:
        logger.warning(
            "voice_translation_failed",
            error=str(e),
            target_language=target_language
        )
        # Fall back to English if translation fails
        return text
