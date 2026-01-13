"""Language detection utilities."""

from typing import Optional

SUPPORTED_LANGUAGES = {"fr", "en", "es", "de"}  # Français, Anglais, Espagnol, Allemand


def detect_language(text: str, min_words: int = 8) -> str:
    """
    Detect the language of a text.
    
    Args:
        text: Text to analyze
        min_words: Minimum number of words required for detection
    
    Returns:
        Language code (default: 'fr' if detection fails or not enough words)
    """
    try:
        from langdetect import detect
        
        words = text.split()
        if len(words) < min_words:
            return "fr"
        
        detected = detect(text)
        
        # Only return if detected language is supported and different from French
        if detected in SUPPORTED_LANGUAGES and detected != "fr":
            return detected
        
        return "fr"
    except ImportError:
        # langdetect not installed, default to French
        return "fr"
    except Exception:
        # Detection failed, default to French
        return "fr"
