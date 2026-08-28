import os

from django.db.models.signals import post_save

from saml2_auth.models import SAMLMetadataModel
from tfc.settings.settings import BASE_DIR


def _create_meta_file(sender, instance, created, **kwargs):
    """
    Creating local file for meta.
    """
    if instance.meta:
        meta_dir = os.path.join(
            BASE_DIR,
            "metadata",
        )
        alias = instance._state.db
        if not os.path.exists(meta_dir):
            os.makedirs(meta_dir)
        meta_file_path = os.path.join(meta_dir, f"{alias}.xml")
        with open(meta_file_path, "w") as fh:
            fh.write(instance.meta)


post_save.connect(_create_meta_file, SAMLMetadataModel)
