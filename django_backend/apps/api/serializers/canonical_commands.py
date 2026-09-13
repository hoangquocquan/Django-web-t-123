"""Strict input contracts for Phase 4B canonical command endpoints."""

from __future__ import annotations

import re
from decimal import Decimal

from rest_framework import serializers


UNIT_CHOICES = ("PCS", "KG", "M", "MM")
CUSTOMER_STATUS_CHOICES = ("ACTIVE", "INACTIVE")
REQUESTED_FIELD_CHOICES = {
    "project_name",
    "notes",
    "quote_due_at",
    "required_delivery_date",
    "lines",
    "documents",
}
PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")


class StrictSerializer(serializers.Serializer):
    """Reject undeclared command fields instead of silently ignoring them."""

    def to_internal_value(self, data):
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise serializers.ValidationError(
                {"unknown_fields": [f"Unsupported field: {name}" for name in unknown]}
            )
        return super().to_internal_value(data)


class ContactFieldsMixin:
    """Normalize the permissive international phone contract."""

    def validate_phone(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        normalized = re.sub(r"[\s().-]", "", raw)
        if not PHONE_PATTERN.fullmatch(normalized):
            raise serializers.ValidationError(
                "Phone must contain 7 to 15 digits with an optional leading plus."
            )
        return normalized

    def validate_email(self, value):
        return str(value or "").strip().casefold()


class CustomerCreateSerializer(ContactFieldsMixin, StrictSerializer):
    company_name = serializers.CharField(max_length=220, trim_whitespace=True)
    contact_name = serializers.CharField(
        max_length=160, required=False, allow_blank=True, default=""
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(
        max_length=80, required=False, allow_blank=True, default=""
    )
    country = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default="Vietnam"
    )
    status = serializers.ChoiceField(
        choices=CUSTOMER_STATUS_CHOICES, required=False, default="ACTIVE"
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CustomerUpdateSerializer(ContactFieldsMixin, StrictSerializer):
    company_name = serializers.CharField(max_length=220, required=False)
    contact_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=80, required=False, allow_blank=True)
    country = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        return attrs


class EmptyCommandSerializer(StrictSerializer):
    pass


class ReasonSerializer(StrictSerializer):
    reason = serializers.CharField(trim_whitespace=True)


class PartCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=220, trim_whitespace=True)
    revision = serializers.CharField(max_length=32, trim_whitespace=True)
    unit = serializers.ChoiceField(choices=UNIT_CHOICES)
    default_material_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    tolerance = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    technical_requirements = serializers.CharField(required=False, allow_blank=True, default="")


class PartUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=220, required=False)
    revision = serializers.CharField(max_length=32, required=False)
    unit = serializers.ChoiceField(choices=UNIT_CHOICES, required=False)
    default_material_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    tolerance = serializers.CharField(max_length=120, required=False, allow_blank=True)
    technical_requirements = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        return attrs


class MaterialCreateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    standard = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    grade = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class MaterialUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=160, required=False)
    standard = serializers.CharField(max_length=120, required=False, allow_blank=True)
    grade = serializers.CharField(max_length=120, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        return attrs


class RfqCreateSerializer(StrictSerializer):
    customer_id = serializers.IntegerField(min_value=1)
    project_name = serializers.CharField(max_length=220, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    quote_due_at = serializers.DateField()
    required_delivery_date = serializers.DateField()
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class RfqUpdateSerializer(StrictSerializer):
    project_name = serializers.CharField(max_length=220, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    quote_due_at = serializers.DateField(required=False)
    required_delivery_date = serializers.DateField(required=False)
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        return attrs


class RfqLineSerializer(StrictSerializer):
    part_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    material_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(
        max_digits=16, decimal_places=4, required=False, min_value=Decimal("0.0001")
    )
    unit = serializers.ChoiceField(choices=UNIT_CHOICES, required=False)
    required_delivery_date = serializers.DateField(required=False)
    tolerance = serializers.CharField(max_length=120, required=False, allow_blank=True)
    technical_notes = serializers.CharField(required=False, allow_blank=True)
    drawing_required = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one line field is required.")
        return attrs


class RfqLineCreateSerializer(RfqLineSerializer):
    description = serializers.CharField()
    quantity = serializers.DecimalField(
        max_digits=16, decimal_places=4, min_value=Decimal("0.0001")
    )
    unit = serializers.ChoiceField(choices=UNIT_CHOICES)
    required_delivery_date = serializers.DateField()


class RequestInformationSerializer(StrictSerializer):
    reason = serializers.CharField(trim_whitespace=True)
    requested_fields = serializers.ListField(
        child=serializers.CharField(max_length=64), allow_empty=False, max_length=20
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_requested_fields(self, value):
        normalized = []
        for item in value:
            field = str(item).strip()
            if field not in REQUESTED_FIELD_CHOICES:
                raise serializers.ValidationError(f"Unsupported requested field: {field}")
            if field not in normalized:
                normalized.append(field)
        return normalized


class CompleteReviewSerializer(StrictSerializer):
    feasible_line_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )
    drawing_not_required_line_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, default=list
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class RfqDocumentUploadSerializer(StrictSerializer):
    file = serializers.FileField()
    rfq_line_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    document_revision = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )


class CommercialDecimalField(serializers.DecimalField):
    """Reject JSON floats before Decimal normalization can hide their origin."""

    def to_internal_value(self, data):
        if isinstance(data, float):
            raise serializers.ValidationError("Binary floating-point values are not accepted.")
        return super().to_internal_value(data)


class QuotationPricingLineSerializer(StrictSerializer):
    source_rfq_line_id = serializers.IntegerField(min_value=1)
    unit_price = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0.0001"),
    )
    discount = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )


class QuotationCreateSerializer(StrictSerializer):
    currency = serializers.ChoiceField(choices=("VND", "USD"))
    valid_from = serializers.DateField()
    valid_until = serializers.DateField()
    discount_total = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )
    tax_amount = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0"),
    )
    terms = serializers.CharField(required=False, allow_blank=True, default="")
    lines = QuotationPricingLineSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        if attrs["valid_until"] < attrs["valid_from"]:
            raise serializers.ValidationError(
                {"valid_until": "Validity end must not precede validity start."}
            )
        return attrs


class QuotationUpdateSerializer(StrictSerializer):
    currency = serializers.ChoiceField(choices=("VND", "USD"), required=False)
    valid_from = serializers.DateField(required=False)
    valid_until = serializers.DateField(required=False)
    discount_total = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0"),
        required=False,
    )
    tax_amount = CommercialDecimalField(
        max_digits=20,
        decimal_places=4,
        min_value=Decimal("0"),
        required=False,
    )
    terms = serializers.CharField(required=False, allow_blank=True)
    lines = QuotationPricingLineSerializer(many=True, allow_empty=False, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one editable field is required.")
        if (
            "valid_from" in attrs
            and "valid_until" in attrs
            and attrs["valid_until"] < attrs["valid_from"]
        ):
            raise serializers.ValidationError(
                {"valid_until": "Validity end must not precede validity start."}
            )
        return attrs


class QuotationApprovalSerializer(StrictSerializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class QuotationRejectionSerializer(StrictSerializer):
    reason = serializers.CharField(trim_whitespace=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class QuotationSendSerializer(StrictSerializer):
    sent_to = serializers.CharField(max_length=254, trim_whitespace=True)
    evidence = serializers.CharField(trim_whitespace=True)


class QuotationCustomerDecisionSerializer(StrictSerializer):
    contact_snapshot = serializers.CharField(max_length=254, trim_whitespace=True)
    evidence = serializers.CharField(trim_whitespace=True)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
