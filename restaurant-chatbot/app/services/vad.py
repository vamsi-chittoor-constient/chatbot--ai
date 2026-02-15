"""
Voice Activity Detection (VAD) Abstraction Layer

Supports multiple VAD engines configurable via environment variable:
- silero: Silero VAD (default) - Best multilingual support, trained on 6000+ languages
- ten: TEN VAD - Lower latency, better accuracy on short pauses
- webrtc: WebRTC VAD - Lightweight, minimal resource usage

Set VAD_ENGINE environment variable to select the engine.
"""
import os
import numpy as np
import structlog
from abc import ABC, abstractmethod
from typing import Optional

logger = structlog.get_logger(__name__)

# Environment variable for VAD engine selection
VAD_ENGINE = os.getenv("VAD_ENGINE", "silero").lower()


class BaseVAD(ABC):
    """Abstract base class for VAD implementations"""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def detect_speech(self, audio_float32: np.ndarray, sample_rate: int = 16000) -> float:
        """
        Detect speech probability in audio chunk.

        Args:
            audio_float32: Audio data as float32 numpy array (normalized to -1.0 to 1.0)
            sample_rate: Audio sample rate (default 16kHz)

        Returns:
            Speech probability between 0.0 and 1.0
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset VAD state (if stateful)"""
        pass


class SileroVAD(BaseVAD):
    """
    Silero VAD - Deep learning based VAD

    Pros:
    - Trained on 6000+ languages (excellent for Hindi, Tamil, etc.)
    - High accuracy in noisy environments
    - Good for multilingual applications

    Cons:
    - Higher latency than WebRTC
    - Larger model size (~2MB)
    """

    def __init__(self):
        import torch
        from silero_vad import load_silero_vad

        logger.info("Loading Silero VAD model...")
        self.model = load_silero_vad()
        self.torch = torch
        logger.info("Silero VAD model loaded successfully")

    def detect_speech(self, audio_float32: np.ndarray, sample_rate: int = 16000) -> float:
        audio_tensor = self.torch.from_numpy(audio_float32)
        return self.model(audio_tensor, sample_rate).item()

    def reset(self):
        # Silero VAD is mostly stateless per-call
        pass


class TenVAD(BaseVAD):
    """
    TEN VAD - Frame-level speech activity detection

    Pros:
    - Lower latency than Silero (agent-friendly)
    - Better accuracy on short pauses
    - Smaller model size (~300-700KB)
    - Language-agnostic (works on audio frames)

    Cons:
    - May need threshold tuning for specific domains
    - Requires ONNX runtime
    """

    def __init__(self):
        try:
            import onnxruntime as ort

            logger.info("Loading TEN VAD model...")

            # TEN VAD model path - download if not exists
            model_path = self._get_model_path()

            # Create ONNX inference session
            self.session = ort.InferenceSession(
                model_path,
                providers=['CPUExecutionProvider']
            )

            # Get input/output names
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            # Frame size for TEN VAD (160 samples = 10ms at 16kHz)
            self.frame_size = 160

            logger.info("TEN VAD model loaded successfully")

        except ImportError:
            raise ImportError(
                "TEN VAD requires onnxruntime. Install with: pip install onnxruntime"
            )

    def _get_model_path(self) -> str:
        """Get or download TEN VAD model"""
        import urllib.request

        # Model cache directory
        cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models", "vad")
        os.makedirs(cache_dir, exist_ok=True)

        model_path = os.path.join(cache_dir, "ten_vad.onnx")

        if not os.path.exists(model_path):
            logger.info("Downloading TEN VAD model...")
            # TEN VAD model URL from HuggingFace
            model_url = "https://huggingface.co/TEN-framework/ten-vad/resolve/main/silero_vad.onnx"
            try:
                urllib.request.urlretrieve(model_url, model_path)
                logger.info(f"TEN VAD model downloaded to {model_path}")
            except Exception as e:
                logger.error(f"Failed to download TEN VAD model: {e}")
                raise RuntimeError(
                    f"Failed to download TEN VAD model. "
                    f"Please download manually from {model_url} to {model_path}"
                )

        return model_path

    def detect_speech(self, audio_float32: np.ndarray, sample_rate: int = 16000) -> float:
        # TEN VAD expects specific frame sizes
        # Process the audio and return average probability
        if len(audio_float32) < self.frame_size:
            # Pad if too short
            audio_float32 = np.pad(audio_float32, (0, self.frame_size - len(audio_float32)))

        # Run inference
        input_data = audio_float32.reshape(1, -1).astype(np.float32)
        outputs = self.session.run([self.output_name], {self.input_name: input_data})

        # Return speech probability (output is typically [batch, frames, 1] or similar)
        prob = outputs[0]
        if isinstance(prob, np.ndarray):
            prob = float(np.mean(prob))

        return prob

    def reset(self):
        pass


class WebRTCVAD(BaseVAD):
    """
    WebRTC VAD - Google's lightweight VAD

    Pros:
    - Very lightweight (minimal CPU/memory)
    - Fast processing
    - No deep learning dependencies
    - Good for resource-constrained environments

    Cons:
    - Lower accuracy than Silero/TEN
    - Works best with clean audio
    - Less robust to noise
    """

    def __init__(self, aggressiveness: int = 3):
        """
        Initialize WebRTC VAD.

        Args:
            aggressiveness: How aggressive the VAD is in filtering non-speech (0-3)
                           0 = least aggressive (more false positives)
                           3 = most aggressive (more false negatives)
        """
        try:
            import webrtcvad

            logger.info(f"Loading WebRTC VAD (aggressiveness={aggressiveness})...")
            self.vad = webrtcvad.Vad(aggressiveness)
            self.aggressiveness = aggressiveness
            logger.info("WebRTC VAD loaded successfully")

        except ImportError:
            raise ImportError(
                "WebRTC VAD requires webrtcvad. Install with: pip install webrtcvad"
            )

    def detect_speech(self, audio_float32: np.ndarray, sample_rate: int = 16000) -> float:
        # WebRTC VAD requires specific frame durations: 10, 20, or 30 ms
        # At 16kHz: 160, 320, or 480 samples

        # Convert float32 back to int16 for WebRTC
        audio_int16 = (audio_float32 * 32768).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        # Use 30ms frames (480 samples at 16kHz)
        frame_duration_ms = 30
        frame_size = int(sample_rate * frame_duration_ms / 1000)
        frame_bytes = frame_size * 2  # 2 bytes per sample (int16)

        if len(audio_bytes) < frame_bytes:
            # Pad if too short
            audio_bytes = audio_bytes + b'\x00' * (frame_bytes - len(audio_bytes))

        # Process frames and calculate speech ratio
        speech_frames = 0
        total_frames = 0

        for i in range(0, len(audio_bytes) - frame_bytes + 1, frame_bytes):
            frame = audio_bytes[i:i + frame_bytes]
            if len(frame) == frame_bytes:
                try:
                    is_speech = self.vad.is_speech(frame, sample_rate)
                    speech_frames += int(is_speech)
                    total_frames += 1
                except Exception:
                    pass

        if total_frames == 0:
            return 0.0

        # Return speech probability as ratio of speech frames
        return speech_frames / total_frames

    def reset(self):
        # WebRTC VAD is stateless
        pass


# Global VAD instance (lazy loaded)
_vad_instance: Optional[BaseVAD] = None


def get_vad() -> BaseVAD:
    """
    Get the configured VAD instance (lazy loading).

    The VAD engine is selected via the VAD_ENGINE environment variable:
    - 'silero' (default): Silero VAD - best for multilingual
    - 'ten': TEN VAD - lower latency, better accuracy
    - 'webrtc': WebRTC VAD - lightweight

    Returns:
        BaseVAD instance
    """
    global _vad_instance

    if _vad_instance is None:
        engine = VAD_ENGINE
        logger.info(f"Initializing VAD engine: {engine}")

        try:
            if engine == "silero":
                _vad_instance = SileroVAD()
            elif engine == "ten":
                _vad_instance = TenVAD()
            elif engine == "webrtc":
                _vad_instance = WebRTCVAD()
            else:
                logger.warning(f"Unknown VAD engine '{engine}', falling back to WebRTC")
                _vad_instance = WebRTCVAD()
        except Exception as e:
            logger.warning(f"Failed to load VAD engine '{engine}': {e}. Falling back to WebRTC.")
            _vad_instance = WebRTCVAD()

    return _vad_instance


def detect_speech(audio_float32: np.ndarray, sample_rate: int = 16000) -> float:
    """
    Convenience function to detect speech using the configured VAD.

    Args:
        audio_float32: Audio data as float32 numpy array
        sample_rate: Audio sample rate (default 16kHz)

    Returns:
        Speech probability between 0.0 and 1.0
    """
    vad = get_vad()
    return vad.detect_speech(audio_float32, sample_rate)
