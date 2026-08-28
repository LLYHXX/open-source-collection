from django import forms

from saml2_auth.models import SAMLMetadataModel

# from utils.base.base_admin import BaseAdmin


class SAMLMetadataForm(forms.ModelForm):
    file = forms.FileField(help_text="meta.xml", required=False)

    class Meta:
        model = SAMLMetadataModel
        exclude = ["uuid"]

    def clean(self):
        data = super().clean()
        if "file" in data and data.get("file"):
            meta = data.pop("file").read()
            data["meta"] = meta.decode()
        return data


# class SAMLMetadataAdmin(BaseAdmin):
#     form = SAMLMetadataForm
#     list_display = ('uuid', 'identity_type', 'is_enabled', 'added_on', 'updated_on', 'is_deleted', 'id',)
#     list_per_page = 20
#     list_filter = ('added_on', 'is_enabled', 'is_deleted',)
#     readonly_fields = ('uuid',)


# admin.site.register(SAMLMetadataModel, SAMLMetadataAdmin)
