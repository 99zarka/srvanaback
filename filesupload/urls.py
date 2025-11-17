from django.urls import path
from .views import FileUploadView, ImageUploadView

urlpatterns = [
    path('upload/file/', FileUploadView.as_view(), name='file-upload'),
    path('upload/image/', ImageUploadView.as_view(), name='image-upload'),
]
