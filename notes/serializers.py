from rest_framework import serializers
from .models import Note
from .models import ActivityLog
from .models import Collaboration
from notes.models import NoteInvitee
from .models import Note, NoteHistory

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'

class CollaborationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collaboration
        fields = '__all__'

class NoteInviteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteInvitee
        fields = ['id', 'note', 'user', 'status']
        read_only_fields = ['id', 'note']

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

class NoteHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteHistory
        fields = '__all__'