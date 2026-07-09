from rest_framework import viewsets

from .models import Reference
from .serializers import ReferenceSerializer


class ReferenceViewSet(viewsets.ModelViewSet):
    """
    Bibliographic registry CRUD.
      GET/POST /api/references/          — list · create
      GET/PATCH/DELETE /api/references/{id}/
    Reads are public; writes need a login (DRF default IsAuthenticatedOrReadOnly).
    """
    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer
