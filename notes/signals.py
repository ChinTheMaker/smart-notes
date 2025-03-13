from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Note, NoteHistory
from django.utils.timezone import now

@receiver(pre_save, sender=Note)
def save_note_history(sender, instance, **kwargs):
    if instance.pk:  # Ensure it's an update, not a new note
        old_note = Note.objects.get(pk=instance.pk)
        if old_note.content != instance.content:  # Only save if content changes
            NoteHistory.objects.create(
                note=old_note,
                content=old_note.content,
                timestamp=now()
            )
