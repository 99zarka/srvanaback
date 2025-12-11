from rest_framework import serializers
import cloudinary.uploader
import re

class CloudinaryImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Check if data is already a URL
        if isinstance(data, str) and (data.startswith('http') or data.startswith('https')):
            # If it's already a URL, return it directly
            return data
        # If it's a file object, perform the Cloudinary upload
        try:
            upload_result = cloudinary.uploader.upload(data)
            return upload_result['secure_url']
        except Exception as e:
            raise serializers.ValidationError(f"Cloudinary upload failed: {e}")

class CloudinaryFileField(serializers.FileField):
    def to_internal_value(self, data):
        # Check if data is already a URL
        if isinstance(data, str) and (data.startswith('http') or data.startswith('https')):
            # If it's already a URL, return it directly
            return data
        # If it's a file object, perform the Cloudinary upload
        try:
            upload_result = cloudinary.uploader.upload(data)
            return upload_result['secure_url']
        except Exception as e:
            raise serializers.ValidationError(f"Cloudinary upload failed: {e}")
