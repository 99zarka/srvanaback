from rest_framework import serializers
from .models import Payment, PaymentMethod

class PaymentMethodSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = ['id', 'user', 'masked_pan', 'card_type', 'expiration_date', 'card_holder_name', 'email', 'is_default', 'image']
        read_only_fields = ['masked_pan', 'card_type', 'expiration_date', 'email', 'image'] # These are populated via Webhook or readonly

    def get_image(self, obj):
        # Return a static URL or asset path for the card logo
        card_type = (obj.card_type or "").lower()
        if "visa" in card_type:
            return "https://raw.githubusercontent.com/muhammederdem/credit-card-form/master/src/assets/images/visa.png"
        elif "master" in card_type:
            return "https://raw.githubusercontent.com/muhammederdem/credit-card-form/master/src/assets/images/mastercard.png"
        elif "amex" in card_type:
             return "https://raw.githubusercontent.com/muhammederdem/credit-card-form/master/src/assets/images/amex.png"
        return "https://raw.githubusercontent.com/muhammederdem/credit-card-form/master/src/assets/images/chip.png"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
