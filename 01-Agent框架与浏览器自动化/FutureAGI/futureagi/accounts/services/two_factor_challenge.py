import json
import time
import uuid

import structlog
from django.conf import settings
from django.core.cache import cache

logger = structlog.get_logger(__name__)

CHALLENGE_TTL = getattr(settings, "TWO_FACTOR_CHALLENGE_TTL", 300)
MAX_ATTEMPTS = 5

# Per-email rate limit across all challenges: 15 attempts per 15 minutes.
PER_EMAIL_MAX_ATTEMPTS = 15
PER_EMAIL_WINDOW = 900  # 15 minutes in seconds


def create_challenge(user, available_methods):
    """Create a 2FA challenge token in Redis.
    Returns the challenge ID (UUID string).
    """
    challenge_id = str(uuid.uuid4())
    challenge_data = {
        "user_id": str(user.id),
        "email": getattr(user, "email", ""),
        "methods": available_methods,
        "attempts": 0,
        "created_at": time.time(),
    }
    cache.set(
        f"2fa_challenge:{challenge_id}",
        json.dumps(challenge_data),
        timeout=CHALLENGE_TTL,
    )
    return challenge_id


def validate_challenge(challenge_id, count_attempt=True):
    """Retrieve and validate a challenge token from Redis.
    Returns the challenge data dict if valid, None if expired/missing/exhausted.
    If count_attempt is True, increments attempt count without resetting the TTL.
    If count_attempt is False, only checks validity without incrementing (read-only).
    """
    cache_key = f"2fa_challenge:{challenge_id}"
    raw = cache.get(cache_key)
    if not raw:
        return None

    data = json.loads(raw)

    # Check per-challenge attempts (always check, even for read-only)
    if data["attempts"] >= MAX_ATTEMPTS:
        cache.delete(cache_key)
        logger.warning("2fa_challenge_rate_limited", challenge_id=challenge_id)
        return None

    if not count_attempt:
        return data

    # Per-email rate limit across all challenges (atomic increment)
    email = data.get("email")
    if email:
        email_rate_key = f"2fa_rate:{email}"
        current = cache.get(email_rate_key, 0)
        if current >= PER_EMAIL_MAX_ATTEMPTS:
            logger.warning("2fa_per_email_rate_limited", email=email)
            return None
        try:
            cache.incr(email_rate_key)
        except ValueError:
            # Key doesn't exist yet; initialize and set TTL
            cache.set(email_rate_key, 1, timeout=PER_EMAIL_WINDOW)

    # Increment attempts
    data["attempts"] += 1

    # Preserve the original TTL instead of resetting it.
    # Use cache.ttl() if available (django-redis), otherwise compute from created_at.
    remaining_ttl = None
    if hasattr(cache, "ttl"):
        remaining_ttl = cache.ttl(cache_key)

    if remaining_ttl and remaining_ttl > 0:
        cache.set(cache_key, json.dumps(data), timeout=remaining_ttl)
    else:
        elapsed = time.time() - data["created_at"]
        ttl_left = max(int(CHALLENGE_TTL - elapsed), 1)
        cache.set(cache_key, json.dumps(data), timeout=ttl_left)

    return data


def consume_challenge(challenge_id):
    """Delete the challenge token from Redis (single-use)."""
    cache.delete(f"2fa_challenge:{challenge_id}")
