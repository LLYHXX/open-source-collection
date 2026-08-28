from django import forms
from django.core.validators import FileExtensionValidator

from saml2_auth.models import SAMLMetadataModel
from tfc.utils.validators import sso_name_validator

# OrgChoices = [(organization.id, organization.name) for organization in Organization.objects.all()]


class IDPUploadForm(forms.Form):
    file = forms.FileField(
        label="file",
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["xml"])],
    )
    identity_type = forms.ChoiceField(
        choices=SAMLMetadataModel.IDENTITY_CHOICES, required=False
    )
    relay_state = forms.CharField(required=False)
    is_enabled = forms.BooleanField(required=False)
    name = forms.CharField(required=False)
    organization = forms.CharField(max_length=100, required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("name"):
            try:
                sso_name_validator(cleaned_data.get("name"))
            except Exception as e:
                self.add_error("name", str(e))
        if cleaned_data.get("is_enabled"):
            try:
                int(cleaned_data.get("identity_type"))
                if int(cleaned_data.get("identity_type")) not in dict(
                    SAMLMetadataModel.IDENTITY_CHOICES
                ):
                    self.add_error("identity_type", "Invalid identity type.")
            except TypeError:
                self.add_error("identity_type", "Invalid identity type.")

        # if cleaned_data.get('relay_state'):
        #     try:
        #         pass
        #     except TypeError:
        #         self.add_error(
        #             'relay_state',
        #             'Invalid relay state.'
        #         )
