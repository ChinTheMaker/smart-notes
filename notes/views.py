from rest_framework.response import Response
import datetime

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

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
        note.priority = request.data.get("priority", "medium")
        note.save()
        return Response({"message": f"Note priority set to {note.priority}"})
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

# Recommend tags based on content
@api_view(['POST'])
def recommend_related_notes(request):
    try:
        note_id = request.data.get("id")
        note = Note.objects.get(pk=note_id)

        # Find related notes based on similar tags
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

# Additional Non-CRUD Endpoints

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
def tag_usage_report(request):
    tags = Note.objects.values_list("tags", flat=True)
    tag_count = {}
    for tag_list in tags:
        for tag in tag_list.split(','):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    return Response(tag_count)

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

        # Validate the reminder_time format
        try:
            reminder_datetime = datetime.datetime.fromisoformat(reminder_time)
        except ValueError:
            return Response({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            status=status.HTTP_400_BAD_REQUEST)

        note.reminder_time = reminder_datetime
        note.save()

        return Response({"message": "Reminder set successfully"}, status=status.HTTP_200_OK)

    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

def identify_most_active_hours(request):
    active_hours = (
        NoteActivity.objects
        .annotate(hour=Hour('timestamp'))  # Extract hour from timestamp
        .values('hour')
        .annotate(activity_count=Count('id'))
        .order_by('-activity_count')  # Sort by most active
    )

    if not active_hours.exists():
        return JsonResponse({"error": "No activity data found"}, status=404)

    return JsonResponse(list(active_hours), safe=False)

def activity_report(request):
    data = {"message": "Most active hours report data will be here"}
    return JsonResponse(data)

def track_tag_usage(request):
    return JsonResponse({"message": "Tag usage tracking report"}, safe=False)


@api_view(['GET'])
def filter_notes_by_tag(request, tag):
    notes = Note.objects.filter(tags__icontains=tag)  # Fix filter to match tag
    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def filter_notes_by_date(request):
    date_str = request.GET.get('date')  # Expecting query parameter: ?date=YYYY-MM-DD
    if not date_str:
        return Response({'error': 'Date parameter is required'}, status=400)

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        notes = Note.objects.filter(created_at__date=date)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

@api_view(["GET", "POST"])
def collaborate_on_note(request, note_id):
    try:
        note = Note.objects.get(pk=note_id)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        # Return the list of collaborators
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
        # Get the note by its ID
        note = Note.objects.get(pk=id)

        # Get the action from the request, default to 'updated' if not provided
        action = request.data.get("action", "updated")

        # Get the user_id from the request data
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        # Ensure the user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Create the ActivityLog with the user, note, and action
        activity = ActivityLog.objects.create(note=note, user=user, action=action)

        # Return the success response with serialized activity data
        return Response({"message": "Activity logged successfully", "log": ActivityLogSerializer(activity).data})

    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Get activity logs for a note
@api_view(['GET'])
def get_activity_log(request, id):
    try:
        # Get the note by its ID
        note = Note.objects.get(pk=id)

        # Retrieve all logs associated with the note
        logs = ActivityLog.objects.filter(note=note)

        # If no logs are found, return a message saying so
        if not logs.exists():
            return Response({"message": "No activity found"}, status=404)

        # Return the logs serialized in the response
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

# 1. Auto-Archive Old Notes
@api_view(["POST"])
def auto_archive_notes(request):
    print("Running auto_archive_notes...")  # Debugging line

    # Fetch old notes
    notes_to_archive = Note.objects.filter(is_archived=False, updated_at__lt=now() - timedelta(days=30))

    print(f"Found {notes_to_archive.count()} notes to archive.")  # Debugging line

    archived_notes = []
    for note in notes_to_archive:
        note.is_archived = True
        note.save()
        archived_notes.append({"id": note.id, "title": note.title})

    print(f"Archived {len(archived_notes)} notes.")  # Debugging line

    return Response({"message": f"Archived {len(archived_notes)} notes", "archived_notes": archived_notes})

# 2. Generate a Summary of a Note (Mock AI Summary)
@api_view(['POST'])
def generate_note_summary(request, id):
    note = get_object_or_404(Note, id=id)
    summary = f"Summary: {note.content[:100]}..."  # Mock summary by truncating content
    return Response({"note_id": note.id, "summary": summary}, status=status.HTTP_200_OK)

# 3. Get Note Revision History
@api_view(['GET'])
def get_note_revisions(request, id):
    note = get_object_or_404(Note, id=id)
    revisions = NoteHistory.objects.filter(note=note).order_by('-timestamp')
    serializer = NoteHistorySerializer(revisions, many=True)
    return Response({"note_id": note.id, "revisions": serializer.data}, status=status.HTTP_200_OK)

# 4. Restore Archived Notes
@api_view(['POST'])
def restore_archived_note(request, id):  # Ensure `id` is accepted
    try:
        print(f"Received request to restore note with ID: {id}")  # Debug log

        note = get_object_or_404(Note, id=id)
        note.is_archived = False
        note.save()

        print("Note restored successfully!")  # Debug log
        return Response({"message": "Note restored successfully."})

    except Exception as e:
        print(f"Error restoring note: {e}")  # Debug log
        return Response({"error": str(e)}, status=500)


