from django.urls import re_path

from tfc.ee_stub import EEFeatureNotAvailableView

urlpatterns = [
    re_path(r"^.*$", EEFeatureNotAvailableView.as_view()),
]
