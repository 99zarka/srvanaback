from rest_framework import serializers
import cloudinary.uploader

class CloudinaryImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Perform the Cloudinary upload
        try:
            upload_result = cloudinary.uploader.upload(data)
            return upload_result['secure_url']
        except Exception as e:
            raise serializers.ValidationError(f"Cloudinary upload failed: {e}")

class CloudinaryFileField(serializers.FileField):
    def to_internal_value(self, data):
        # Perform the Cloudinary upload
        try:
            upload_result = cloudinary.uploader.upload(data)
            return upload_result['secure_url']
        except Exception as e:
            raise serializers.ValidationError(f"Cloudinary upload failed: {e}")
