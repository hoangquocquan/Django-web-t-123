"""Public website forms.

These forms keep browser input validation inside Django before the data is
stored as a safe submission intent.
"""

from django import forms


class ContactForm(forms.Form):
    """Validate the public contact form."""

    name = forms.CharField(label="Name", max_length=160)
    company = forms.CharField(label="Company", max_length=220, required=False)
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Phone", max_length=80, required=False)
    country = forms.CharField(label="Country", max_length=120, required=False)
    interested_product = forms.CharField(label="Interested product", max_length=220, required=False)
    message = forms.CharField(label="Message", widget=forms.Textarea, required=False)
    captcha_answer = forms.CharField(label="Captcha: 3 + 4", max_length=10)

    def clean(self):
        """Require at least one contact channel and a simple captcha answer."""
        cleaned = super().clean()
        if not (cleaned.get("email") or cleaned.get("phone")):
            raise forms.ValidationError("Email or phone is required.")
        if str(cleaned.get("captcha_answer") or "").strip() != "7":
            raise forms.ValidationError("Captcha answer is not valid.")
        return cleaned


class QuoteRequestForm(forms.Form):
    """Validate a compact public quote request form."""

    name = forms.CharField(label="Name", max_length=160)
    company = forms.CharField(label="Company", max_length=220, required=False)
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Phone", max_length=80, required=False)
    product = forms.CharField(label="Product", max_length=220, required=False)
    quantity = forms.CharField(label="Quantity", max_length=80, required=False)
    tolerance = forms.CharField(label="Tolerance", max_length=120, required=False)
    deadline = forms.CharField(label="Deadline", max_length=120, required=False)
    message = forms.CharField(label="Message", widget=forms.Textarea, required=False)
    captcha_answer = forms.CharField(label="Captcha: 3 + 4", max_length=10)

    def clean(self):
        """Require contact information, quote content, and valid captcha."""
        cleaned = super().clean()
        if not (cleaned.get("email") or cleaned.get("phone")):
            raise forms.ValidationError("Email or phone is required.")
        if not (cleaned.get("product") or cleaned.get("message")):
            raise forms.ValidationError("Product or message is required.")
        if str(cleaned.get("captcha_answer") or "").strip() != "7":
            raise forms.ValidationError("Captcha answer is not valid.")
        return cleaned
