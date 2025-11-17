from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from filesupload.serializers.fields import CloudinaryImageField, CloudinaryFileField
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class FileUploadSerializer(serializers.Serializer):
    file = CloudinaryFileField(required=True, help_text="Select a file to upload to Cloudinary.")

class ImageUploadSerializer(serializers.Serializer):
    image = CloudinaryImageField(required=True, help_text="Select an image file to upload to Cloudinary.")

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        request_body=FileUploadSerializer,
        responses={
            201: openapi.Response('File uploaded successfully', FileUploadSerializer),
            400: 'Bad Request'
        },
        operation_description="Uploads a general file to Cloudinary and returns its URL."
    )
    def post(self, request, format=None):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            # The CloudinaryFileField already handled the upload and returned the secure_url
            file_url = serializer.validated_data['file']
            return Response({'message': 'File uploaded successfully', 'url': file_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        request_body=ImageUploadSerializer,
        responses={
            201: openapi.Response('Image uploaded successfully', ImageUploadSerializer),
            400: 'Bad Request'
        },
        operation_description="Uploads an image file to Cloudinary and returns its URL."
    )
    def post(self, request, format=None):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            # The CloudinaryImageField already handled the upload and returned the secure_url
            image_url = serializer.validated_data['image']
            return Response({'message': 'Image uploaded successfully', 'url': image_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
