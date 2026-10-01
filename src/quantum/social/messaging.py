"""quantum.social.messaging — Messaging integrations for social engineering.

Supports WhatsApp, iMessage, Telegram, Snapchat, and SMS with AI-driven
social engineering attacks using spoofing, cloned voice, and cloned face.
FOR AUTHORIZED SECURITY TESTING AND RESEARCH ONLY.
"""
from __future__ import annotations

from datetime import datetime

from quantum.core.logging import log

MESSAGING_PLATFORMS = {
    "whatsapp": {
        "name": "WhatsApp",
        "type": "messaging",
        "api": "Twilio WhatsApp API / WhatsApp Business API",
        "features": ["text", "media", "voice", "video", "location", "contacts"],
        "spoofing": ["caller_id", "message_template", "profile_clone"],
        "cloning": ["voice_clone", "face_clone", "message_style"],
        "social_engineering": ["phishing", "pretexting", "baiting", "quid_pro_quo"],
    },
    "imessage": {
        "name": "iMessage",
        "type": "messaging",
        "api": "AppleScript / private API",
        "features": ["text", "media", "voice", "video", "location", "contacts"],
        "spoofing": ["caller_id", "message_template", "profile_clone"],
        "cloning": ["voice_clone", "face_clone", "message_style"],
        "social_engineering": ["phishing", "pretexting", "baiting", "quid_pro_quo"],
    },
    "telegram": {
        "name": "Telegram",
        "type": "messaging",
        "api": "Telegram Bot API / TDLib",
        "features": ["text", "media", "voice", "video", "location", "contacts"],
        "spoofing": ["caller_id", "message_template", "profile_clone"],
        "cloning": ["voice_clone", "face_clone", "message_style"],
        "social_engineering": ["phishing", "pretexting", "baiting", "quid_pro_quo"],
    },
    "snapchat": {
        "name": "Snapchat",
        "type": "messaging",
        "api": "Snap Kit / private API",
        "features": ["text", "media", "voice", "video", "location", "contacts"],
        "spoofing": ["caller_id", "message_template", "profile_clone"],
        "cloning": ["voice_clone", "face_clone", "message_style"],
        "social_engineering": ["phishing", "pretexting", "baiting", "quid_pro_quo"],
    },
    "sms": {
        "name": "SMS",
        "type": "messaging",
        "api": "Twilio SMS API / SendGrid SMS API",
        "features": ["text", "media", "voice", "video", "location", "contacts"],
        "spoofing": ["caller_id", "message_template", "profile_clone"],
        "cloning": ["voice_clone", "face_clone", "message_style"],
        "social_engineering": ["phishing", "pretexting", "baiting", "quid_pro_quo"],
    },
}

SOCIAL_ENGINEERING_TECHNIQUES = {
    "phishing": {
        "name": "Phishing",
        "description": "Deceptive messages to trick targets into revealing credentials",
        "vectors": ["email", "sms", "social_media", "messaging_apps"],
        "payloads": ["credential_harvest", "malware_delivery", "payment_fraud"],
    },
    "pretexting": {
        "name": "Pretexting",
        "description": "Fabricated scenarios to manipulate targets",
        "vectors": ["phone", "email", "in_person", "messaging_apps"],
        "payloads": ["information_disclosure", "access_grant", "financial_fraud"],
    },
    "baiting": {
        "name": "Baiting",
        "description": "Offering something enticing to trick targets",
        "vectors": ["usb", "download", "email", "messaging_apps"],
        "payloads": ["malware_infection", "credential_theft", "ransomware"],
    },
    "quid_pro_quo": {
        "name": "Quid Pro Quo",
        "description": "Offering a service in exchange for information",
        "vectors": ["phone", "email", "messaging_apps"],
        "payloads": ["credential_harvest", "access_grant", "information_disclosure"],
    },
    "tailgating": {
        "name": "Tailgating",
        "description": "Following authorized personnel into restricted areas",
        "vectors": ["physical", "digital"],
        "payloads": ["unauthorized_access", "data_theft", "espionage"],
    },
    "watering_hole": {
        "name": "Watering Hole",
        "description": "Compromising websites frequently visited by targets",
        "vectors": ["website", "social_media", "messaging_apps"],
        "payloads": ["malware_infection", "credential_theft", "espionage"],
    },
}

VOICE_CLONE_PROVIDERS = {
    "xtts": {
        "name": "XTTS-v2",
        "type": "local",
        "description": "Coqui TTS voice cloning",
        "github": "https://github.com/coqui-ai/TTS",
        "features": ["voice_clone", "text_to_speech", "multi_language"],
    },
    "rvc": {
        "name": "RVC (Retrieval-based Voice Conversion)",
        "type": "local",
        "description": "Voice conversion with trained models",
        "github": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
        "features": ["voice_conversion", "real_time", "multi_language"],
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "type": "cloud",
        "description": "AI voice cloning and text-to-speech",
        "features": ["voice_clone", "text_to_speech", "multi_language", "emotion"],
    },
    "playht": {
        "name": "PlayHT",
        "type": "cloud",
        "description": "AI voice generation and cloning",
        "features": ["voice_clone", "text_to_speech", "multi_language"],
    },
}

FACE_CLONE_PROVIDERS = {
    "deepfacelab": {
        "name": "DeepFaceLab",
        "type": "local",
        "description": "Deepfake face swapping",
        "github": "https://github.com/iperov/DeepFaceLab",
        "features": ["face_swap", "face_reenactment", "deepfake"],
    },
    "faceswap": {
        "name": "FaceSwap",
        "type": "local",
        "description": "Open source face swapping",
        "github": "https://github.com/deepfakes/faceswap",
        "features": ["face_swap", "face_reenactment", "deepfake"],
    },
    "roop": {
        "name": "Roop",
        "type": "local",
        "description": "One-click face swap",
        "github": "https://github.com/s0md3v/roop",
        "features": ["face_swap", "one_click", "deepfake"],
    },
    "simswap": {
        "name": "SimSwap",
        "type": "local",
        "description": "Face swapping for images and videos",
        "github": "https://github.com/neuralchen/SimSwap",
        "features": ["face_swap", "image", "video", "deepfake"],
    },
}


def list_messaging_platforms() -> dict:
    """List all messaging platforms and their capabilities."""
    return MESSAGING_PLATFORMS


def list_social_engineering_techniques() -> dict:
    """List all social engineering techniques."""
    return SOCIAL_ENGINEERING_TECHNIQUES


def list_voice_clone_providers() -> dict:
    """List all voice cloning providers."""
    return VOICE_CLONE_PROVIDERS


def list_face_clone_providers() -> dict:
    """List all face cloning providers."""
    return FACE_CLONE_PROVIDERS


def generate_social_engineering_campaign(platform: str, technique: str,
                                          target: str, ai_provider: str = "abliteratus") -> dict:
    """Generate a social engineering campaign configuration."""
    if platform not in MESSAGING_PLATFORMS:
        return {"error": f"Unknown platform: {platform}. Available: {list(MESSAGING_PLATFORMS.keys())}"}
    if technique not in SOCIAL_ENGINEERING_TECHNIQUES:
        return {"error": f"Unknown technique: {technique}. Available: {list(SOCIAL_ENGINEERING_TECHNIQUES.keys())}"}
    platform_info = MESSAGING_PLATFORMS[platform]
    technique_info = SOCIAL_ENGINEERING_TECHNIQUES[technique]
    out = {
        "platform": platform,
        "platform_name": platform_info["name"],
        "technique": technique,
        "technique_name": technique_info["name"],
        "target": target,
        "ai_provider": ai_provider,
        "generated_at": datetime.now().isoformat(),
        "config": {
            "spoofing": platform_info["spoofing"],
            "cloning": platform_info["cloning"],
            "payloads": technique_info["payloads"],
            "vectors": technique_info["vectors"],
        },
        "voice_clone": VOICE_CLONE_PROVIDERS,
        "face_clone": FACE_CLONE_PROVIDERS,
        "message_templates": _generate_message_templates(technique, platform),
    }
    log(f"Social engineering campaign: {technique} via {platform} targeting {target}", "SOCIAL")
    return out


def _generate_message_templates(technique: str, platform: str) -> list:
    """Generate message templates for the specified technique and platform."""
    templates = []
    if technique == "phishing":
        templates = [
            "Urgent: Your account has been compromised. Verify your identity here: [link]",
            "Security Alert: Unusual activity detected. Login to secure your account: [link]",
            "Package Delivery Failed. Update your shipping info: [link]",
            "Invoice Overdue. View and pay now: [link]",
        ]
    elif technique == "pretexting":
        templates = [
            "Hi, this is IT support. We need to verify your credentials for a security update.",
            "Hello, I'm from billing. There's an issue with your account. Can you confirm your details?",
            "Hi, this is your manager. I need you to process an urgent payment. Here are the details...",
        ]
    elif technique == "baiting":
        templates = [
            "Free gift card! Click here to claim: [link]",
            "You've won a prize! Enter your details to claim: [link]",
            "Exclusive offer just for you! Limited time: [link]",
        ]
    elif technique == "quid_pro_quo":
        templates = [
            "I can help you with that if you provide your login credentials.",
            "I'll fix your account issue if you verify your identity here: [link]",
            "Let me assist you. Just confirm your account details.",
        ]
    return templates


def messaging_dashboard_state() -> dict:
    """Return the full messaging dashboard state for the UI."""
    return {
        "platforms": MESSAGING_PLATFORMS,
        "techniques": SOCIAL_ENGINEERING_TECHNIQUES,
        "voice_clone_providers": VOICE_CLONE_PROVIDERS,
        "face_clone_providers": FACE_CLONE_PROVIDERS,
        "active_campaigns": [],
        "generated_at": datetime.now().isoformat(),
    }
