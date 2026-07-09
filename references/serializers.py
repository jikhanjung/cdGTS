from rest_framework import serializers

from .models import Reference


class ReferenceSerializer(serializers.ModelSerializer):
    link = serializers.ReadOnlyField()

    class Meta:
        model = Reference
        fields = ["id", "slug", "doi", "title", "authors", "year", "container", "url", "kind", "note", "link"]
