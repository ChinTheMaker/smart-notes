from django.urls import path
from .views import create_note, get_note, update_note, delete_note
from . import views  # Ensure views.py has all referenced functions
from .views import recommend_related_notes
from .views import set_reminder
from .views import check_workflow_status
from .views import identify_most_active_hours
from .views import activity_report
from .views import track_tag_usage
from .views import search_notes
from .views import filter_notes_by_tag
from .views import filter_notes_by_date
from .views import collaborate_on_note
from .views import invite_user_to_note
from .views import view_invitees
from .views import log_activity
from .views import get_activity_log
from notes.views import NoteInviteeListView
from .views import auto_archive_notes, generate_note_summary, get_note_revisions, restore_archived_note
urlpatterns = [
    path('notes/create/', create_note, name="create-note"),
    path('notes/<int:id>/', get_note, name="get-note"),
    path('notes/<int:id>/update/', update_note, name="update-note"),
    path('notes/<int:id>/delete/', delete_note, name="delete-note"),
    path('notes/<int:id>/archive/', views.archive_note, name="archive-note"),  # Added /
    path('notes/<int:id>/prioritize/', views.prioritize_note, name="prioritize-note"),  # Added /
    path('recommendations/related-notes/', recommend_related_notes, name="recommend_related_notes"),
    path('reports/productivity/', views.productivity_report, name="productivity-report"),  # Added /
    path('workflows/reminders/', set_reminder, name="set_reminder"),
    path('workflows/status/<int:id>/', check_workflow_status, name="check_workflow_status"),
    path('notes/active-hours/', identify_most_active_hours, name='identify-most-active-hours'),
    path("reports/most-active-hours/", activity_report, name="most-active-hours"),
    path('reports/track-tag-usage/', track_tag_usage, name='track-tag-usage'),
    path('notes/search/', search_notes, name='search-notes'),
    path('notes/filter-by-tag/<str:tag>/', filter_notes_by_tag, name='filter-notes-by-tag'),
    path('notes/filter-by-date/', filter_notes_by_date, name='filter-notes-by-date'),
    path("notes/<int:note_id>/collaborate/", collaborate_on_note, name="collaborate-on-note"),
    path('notes/<int:note_id>/invite/', views.invite_user_to_note, name='invite_user'),
    path('notes/<int:id>/invitees/', view_invitees, name='view-invitees'),
    path('notes/<int:id>/log-activity/', log_activity, name='log-activity'),
    path('notes/<int:id>/activity-logs/', get_activity_log, name='get-activity-log'),
    path("api/notes/<int:note_id>/invitees/", NoteInviteeListView.as_view(), name="note-invitees-list"),
    path('notes/auto-archive/', auto_archive_notes, name='auto-archive-notes'),
    path('notes/<int:id>/summary/', generate_note_summary, name='generate-note-summary'),
    path('notes/<int:id>/revisions/', get_note_revisions, name='get-note-revisions'),
    path('notes/<int:id>/restore/', restore_archived_note, name='restore_note'),
]

