from collections.abc import Iterable

# DRF style validation error so we get proper 400 responses in views
from rest_framework import serializers

# Labels that must be unique per PromptTemplate
PROTECTED_LABELS: set[str] = {"production", "staging", "latest"}


def _normalise_labels(raw) -> list[str]:
    """Return a list of labels given a value coming from metadata."""
    if not raw:
        return []

    if isinstance(raw, str):
        return [raw]

    if isinstance(raw, list):
        # Filter falsy values & ensure str
        return [str(v) for v in raw if v]

    # Anything else is invalid
    raise serializers.ValidationError(
        {"metadata": "Label field must be a string, a list of strings, or omitted."}
    )


def ensure_unique_protected_labels(
    template, new_labels: Iterable[str], *, ignore_version: str | None = None
):
    """Validate that none of *new_labels* (intersection with PROTECTED_LABELS)
    already exist on another PromptVersion of *template* (apart from *ignore_version*).

    Raises:
        serializers.ValidationError – when a protected label would be duplicated.
    """

    # Only inspect protected labels
    protected = set(new_labels) & PROTECTED_LABELS
    if not protected:
        return  # Nothing to validate

    from model_hub.models.run_prompt import PromptVersion  # lazy import to avoid cycles

    qs = PromptVersion.objects.filter(original_template=template, deleted=False)
    if ignore_version:
        qs = qs.exclude(template_version=ignore_version)

    for pv in qs:
        existing_raw = pv.metadata.get("label")
        if not existing_raw:
            continue
        existing = _normalise_labels(existing_raw)
        conflict = protected & set(existing)
        if conflict:
            dup_label = next(iter(conflict))
            raise serializers.ValidationError(
                {
                    "metadata": f"Label '{dup_label}' is already assigned to version '{pv.template_version}'. Each protected label may appear on only one version at a time."
                }
            )


def extract_labels_from_metadata(metadata: dict) -> list[str]:
    """Helper to pull labels list from metadata regardless of key format."""
    if not metadata or not isinstance(metadata, dict):
        return []

    raw = metadata.get("label")
    return _normalise_labels(raw)


# ---------------------------------------------------------------------------
# Helpers to mutate versions when protected labels have to move
# ---------------------------------------------------------------------------


def remove_protected_labels_from_versions(
    template, labels_to_remove: Iterable[str], *, ignore_version: str | None = None
):
    """Strip *labels_to_remove* (subset of PROTECTED_LABELS) from every other
    version of *template* except *ignore_version*.

    This is useful when the caller wants to *move* a protected label to a new
    version instead of raising a validation error.
    """

    from model_hub.models.run_prompt import (  # local import to avoid cycles
        PromptVersion,
    )

    labels_set = set(labels_to_remove) & PROTECTED_LABELS
    if not labels_set:
        return

    qs = PromptVersion.objects.filter(original_template=template, deleted=False)
    if ignore_version:
        qs = qs.exclude(template_version=ignore_version)

    for pv in qs:
        raw = pv.metadata.get("label")
        if not raw:
            continue

        labels_existing = _normalise_labels(raw)
        new_labels = [lbl for lbl in labels_existing if lbl not in labels_set]

        # If nothing was removed continue
        if len(new_labels) == len(labels_existing):
            continue

        # Mutate metadata accordingly
        if "label" in pv.metadata:
            if new_labels:
                pv.metadata["label"] = (
                    new_labels[0] if len(new_labels) == 1 else new_labels
                )
            else:
                pv.metadata.pop("label")

        pv.save(update_fields=["metadata", "updated_at"])
