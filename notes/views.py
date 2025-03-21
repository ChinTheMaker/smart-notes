from rest_framework.response import Response
import datetime

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from .models import Reminder
from .serializers import ReminderSerializer
from .models import ActivityLog
from notes.models import Note, Collaboration
from .models import Note, NoteHistory
from .models import NoteActivity
from .models import NoteInvitee
from .models import Workflow
from .serializers import ActivityLogSerializer
from .serializers import NoteInviteeSerializer
from .serializers import NoteSerializer, NoteHistorySerializer
from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from collections import Counter
from datetime import datetime
from notes.models import NoteActivity



# Create a new note
@api_view(['POST'])
def create_note(request):
    serializer = NoteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Retrieve a specific note by ID
@api_view(['GET'])
def get_note(request, id):
    try:
        note = Note.objects.get(pk=id)
        return Response(NoteSerializer(note).data)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

# Update note content or metadata
@api_view(['PUT'])
def update_note(request, id):
    try:
        note = Note.objects.get(pk=id)
        serializer = NoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

# Delete a note
@api_view(['DELETE'])
def delete_note(request, id):
    try:
        note = Note.objects.get(pk=id)
        note.delete()
        return Response({"message": "Note deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

# Archive a note
@api_view(['POST'])
def archive_note(request, id):
    try:
        note = Note.objects.get(pk=id)
        note.is_archived = True
        note.save()
        return Response({"message": "Note archived successfully"})
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

# Prioritize a note
@api_view(['POST'])
def prioritize_note(request, id):
    try:
        note = Note.objects.get(pk=id)

        priority = request.data.get('priority', 'low').lower()

        if priority not in ['high', 'medium', 'low']:
            return Response({"error": "Invalid priority level. Choose from 'high', 'medium', or 'low'."},
                            status=status.HTTP_400_BAD_REQUEST)

        note.priority = priority
        note.save()

        serializer = NoteSerializer(note)

        return Response({
            "message": f"Note priority set to {priority}",
            "note": serializer.data
        }, status=status.HTTP_200_OK)

    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Recommend tags based on content
@api_view(['POST'])
def recommend_related_notes(request):
    try:
        note_id = request.data.get("id")
        note = Note.objects.get(pk=note_id)

        related_notes = Note.objects.filter(tags__icontains=note.tags).exclude(id=note.id)

        return Response(NoteSerializer(related_notes, many=True).data)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Generate a productivity report
@api_view(['GET'])
def productivity_report(request):
    notes_count = Note.objects.count()
    archived_count = Note.objects.filter(is_archived=True).count()
    return Response({"total_notes": notes_count, "archived_notes": archived_count})


# List all active notes
@api_view(['GET'])
def list_active_notes(request):
    active_notes = Note.objects.filter(is_archived=False)
    return Response(NoteSerializer(active_notes, many=True).data)

# Search notes by keyword
@api_view(['GET'])
def search_notes(request):
    keyword = request.GET.get("q", "")
    results = Note.objects.filter(content__icontains=keyword)
    return Response(NoteSerializer(results, many=True).data)

# Retrieve notes by tag
@api_view(['GET'])
def notes_by_tag(request, tag):
    notes = Note.objects.filter(tags__icontains=tag)
    return Response(NoteSerializer(notes, many=True).data)

# Generate a report on tag usage
@api_view(['GET'])
def track_tag_usage(request):
    print("Running latest version of track_tag_usage!")  # Debugging print statement

    tag_strings = Note.objects.values_list('tags', flat=True)

    all_tags = []
    for tag_list in tag_strings:
        if tag_list:
            all_tags.extend([tag.strip().lower() for tag in tag_list.split(',') if tag.strip()])

    tag_count = Counter(all_tags)

    if not tag_count:
        return Response({"message": "No tags found in the system."})

    return Response({
        "tag_usage": dict(tag_count),
        "total_tags_used": len(tag_count)
    })

# Log note activity
@api_view(['POST'])
def log_activity(request, id):
    try:
        note = Note.objects.get(pk=id)
        log = ActivityLog(note=note, action=request.data.get("action", "updated"))
        log.save()
        return Response(ActivityLogSerializer(log).data)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def set_reminder(request):
    try:
        note_id = request.data.get("id")
        reminder_time = request.data.get("reminder_time")

        note = Note.objects.get(pk=note_id)

        try:
            reminder_datetime = datetime.fromisoformat(reminder_time)
        except ValueError:
            return Response({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            status=status.HTTP_400_BAD_REQUEST)

        note.reminder_time = reminder_datetime
        note.save()

        return Response({
            "message": "Reminder set successfully",
            "note_id": note_id,
            "reminder_time": reminder_time,
            "status": "scheduled"
        })

    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# List all reminders
@api_view(['GET'])
def list_reminders(request):
    from notes.models import Reminder
    reminders = Reminder.objects.all()
    serializer = ReminderSerializer(reminders, many=True)
    return Response(serializer.data)

# Get a specific reminder by ID
@api_view(['GET'])
def get_reminder(request, id):
    reminder = get_object_or_404(Reminder, pk=id)
    return Response({
        "id": reminder.id,
        "note_id": reminder.note.id,
        "reminder_time": reminder.reminder_time,
        "status": reminder.status
    })

@api_view(['GET'])
def check_workflow_status(request, id):
    try:
        workflow = Workflow.objects.get(pk=id)
        return Response({
            "id": workflow.id,
            "status": workflow.status,
            "last_updated": workflow.last_updated
        }, status=status.HTTP_200_OK)

    except Workflow.DoesNotExist:
        return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def identify_most_active_hours(request):
    print("View is being called!")
    activities = NoteActivity.objects.all()

    hour_counter = Counter(activity.timestamp.hour for activity in activities)
    most_active_hours = dict(hour_counter)
    peak_hour = max(most_active_hours, key=most_active_hours.get, default=None)
    total_actions = sum(most_active_hours.values())

    return Response({
        "most_active_hours": most_active_hours,
        "peak_hour": peak_hour,
        "total_actions": total_actions
    })

def activity_report(request):
    data = {"message": "Most active hours report data will be here"}
    return JsonResponse(data)

@api_view(['GET'])
def filter_notes_by_tag(request, tag):
    notes = Note.objects.filter(tags__icontains=tag)  # Fix filter to match tag
    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def filter_notes_by_date(request):
    date_str = request.GET.get('date')

    if not date_str:
        return Response({"error": "Date parameter is required in YYYY-MM-DD format."}, status=400)

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        notes = Note.objects.filter(created_at__date=date_obj)

        if not notes.exists():
            return Response({"message": "No notes found for the specified date."})

        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET", "POST"])
def collaborate_on_note(request, note_id):
    try:
        note = Note.objects.get(pk=note_id)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        collaborators = note.collaborations.values_list("user__id", "user__username")
        return Response({"note_id": note.id, "collaborators": list(collaborators)})

    elif request.method == "POST":
        user_ids = request.data.get("user_ids", [])
        users = User.objects.filter(id__in=user_ids)

        for user in users:
            Collaboration.objects.get_or_create(note=note, user=user)  # Prevent duplicates

        return Response({
            "message": f"Users added as collaborators: {user_ids}",
            "note_id": note.id,
            "collaborators": list(note.collaborations.values_list("user_id", flat=True))
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def view_collaborators(request, id):
    note = get_object_or_404(Note, pk=id)
    collaborators = note.collaborations.all().values_list('user__username', flat=True)

    return Response({'collaborators': list(collaborators)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def invite_user_to_note(request, note_id):
    # Logic to invite user
    user_id = request.data.get("user_id")
    # Add the logic to invite the user to the note here (e.g., send an invitation, update database)
    return Response({"message": "User invited successfully!"}, status=status.HTTP_200_OK)



# View Invitees of a Note
@api_view(['GET'])
def view_invitees(request, id):
    try:
        note = get_object_or_404(Note, pk=id)
        invitees = Collaboration.objects.filter(note=note).values_list('user__username', flat=True)
        return Response({"invitees": list(invitees)}, status=status.HTTP_200_OK)
    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)

# Log activity (make sure to pass the user)
@api_view(['POST'])
def log_activity(request, id):
    try:
        note = Note.objects.get(pk=id)

        action = request.data.get("action", "updated")

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        activity = ActivityLog.objects.create(note=note, user=user, action=action)

        return Response({"message": "Activity logged successfully", "log": ActivityLogSerializer(activity).data})

    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Get activity logs for a note
@api_view(['GET'])
def get_activity_log(request, id):
    try:
        note = Note.objects.get(pk=id)

        logs = ActivityLog.objects.filter(note=note)

        if not logs.exists():
            return Response({"message": "No activity found"}, status=404)

        return Response(ActivityLogSerializer(logs, many=True).data)

    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=404)

class NoteInviteeListView(ListAPIView):
    serializer_class = NoteInviteeSerializer

    def get_queryset(self):
        note_id = self.kwargs.get("note_id")  # Fetch the note_id from URL
        print(f"🔍 Debug: Fetching invitees for Note ID: {note_id}")  # Debug log

        invitees = NoteInvitee.objects.filter(note_id=note_id)
        print(f"📌 Debug: Found Invitees - {invitees}")  # Debug log

#auto archive notes
@api_view(["POST"])
def auto_archive_notes(request):
    print("Running auto_archive_notes...")  # Debugging line

    notes_to_archive = Note.objects.filter(is_archived=False, updated_at__lt=now() - timedelta(days=30))

    print(f"Found {notes_to_archive.count()} notes to archive.")  # Debugging line

    archived_notes = []
    for note in notes_to_archive:
        note.is_archived = True
        note.save()
        archived_notes.append({"id": note.id, "title": note.title})

    print(f"Archived {len(archived_notes)} notes.")  # Debugging line

    return Response({"message": f"Archived {len(archived_notes)} notes", "archived_notes": archived_notes})

# Generate a Summary of a Note (Mock AI Summary)
@api_view(['POST'])
def generate_note_summary(request, id):
    note = get_object_or_404(Note, id=id)
    summary = f"Summary: {note.content[:100]}..."  # Mock summary by truncating content
    return Response({"note_id": note.id, "summary": summary}, status=status.HTTP_200_OK)

# Get Note Revision History
@api_view(['GET'])
def get_note_revisions(request, id):
    note = get_object_or_404(Note, id=id)
    revisions = NoteHistory.objects.filter(note=note).order_by('-timestamp')
    serializer = NoteHistorySerializer(revisions, many=True)
    return Response({"note_id": note.id, "revisions": serializer.data}, status=status.HTTP_200_OK)

# Restore Archived Notes
@api_view(['POST'])
def restore_archived_note(request, id):
    try:
        note = Note.objects.get(pk=id, is_archived=True)

        note.is_archived = False
        note.save()

        serializer = NoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Note.DoesNotExist:
        return Response({"error": "Archived note not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})

    return Response({"error": "Invalid credentials"}, status=400)