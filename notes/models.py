from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now



class Note(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=now)
    is_archived = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=[("normal", "Normal"), ("urgent", "Urgent")], default="normal")

    def __str__(self):
        return self.title

class ActivityLog(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.action} on {self.note.title}"


class Workflow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow {self.id}: {self.status}"

class NoteActivity(models.Model):
    ACTIONS = [
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('view', 'Viewed')
    ]

    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.note} on {self.timestamp}"

class Collaboration(models.Model):
        note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="collaborations")
        user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collaborations")
        added_at = models.DateTimeField(auto_now_add=True)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            unique_together = ('note', 'user')  # Ensures a user can't be added twice

        def __str__(self):
            return f"{self.user.username} collaborates on {self.note.title}"

class NoteInvitee(models.Model):
    note = models.ForeignKey('Note', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')])
    email = models.EmailField()

    def __str__(self):
        return f"{self.user.email} - {self.status}"

class NoteHistory(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revision of Note {self.note.id} at {self.timestamp}"