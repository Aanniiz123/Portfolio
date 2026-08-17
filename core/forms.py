from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Contact form tied to the ContactMessage model."""

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "Music video · visualizer · promo"}),
            "message": forms.Textarea(attrs={"placeholder": "Tell me about the track, the vibe, and your deadline…"}),
        }