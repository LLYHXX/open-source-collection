import secrets
import string

import structlog
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from accounts.models.recovery_code import RecoveryCode

logger = structlog.get_logger(__name__)

# Characters for recovery code generation (alphanumeric, no ambiguous chars)
RECOVERY_CODE_CHARS = string.ascii_lowercase + string.digits
RECOVERY_CODE_CHARS = (
    RECOVERY_CODE_CHARS.replace("0", "")
    .replace("o", "")
    .replace("l", "")
    .replace("1", "")
)


def _generate_code():
    """Generate a single recovery code in xxxx-xxxx format."""
    part1 = "".join(secrets.choice(RECOVERY_CODE_CHARS) for _ in range(4))
    part2 = "".join(secrets.choice(RECOVERY_CODE_CHARS) for _ in range(4))
    return f"{part1}-{part2}"


def generate_recovery_codes(user, count=10):
    """Generate new recovery codes for the user.
    Deletes all existing recovery codes first.
    Returns the plaintext codes (shown to user once).
    """
    # Delete all existing codes for this user
    RecoveryCode.objects.filter(user=user).delete()

    plaintext_codes = []
    for _ in range(count):
        code = _generate_code()
        plaintext_codes.append(code)
        RecoveryCode.objects.create(
            user=user,
            code_hash=make_password(code),
            is_used=False,
        )

    return plaintext_codes


def verify_recovery_code(user, code):
    """Verify a recovery code.
    Iterates unused codes, checks with check_password() (constant-time).
    If match: marks code as used. Returns True if valid.
    """
    unused_codes = RecoveryCode.objects.filter(user=user, is_used=False)

    for recovery_code in unused_codes:
        if check_password(code, recovery_code.code_hash):
            recovery_code.is_used = True
            recovery_code.used_at = timezone.now()
            recovery_code.save(update_fields=["is_used", "used_at", "updated_at"])
            return True

    return False


def get_remaining_count(user):
    """Return the count of unused recovery codes for the user."""
    return RecoveryCode.objects.filter(user=user, is_used=False).count()
