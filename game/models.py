from django.db import models
from django.contrib.auth.models import User


class Word(models.Model):
    """A 5-letter uppercase English word used as a game target."""
    word = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ['word']


class Game(models.Model):
    """A single game session for a player."""
    STATUS_ACTIVE = 'active'
    STATUS_WON = 'won'
    STATUS_LOST = 'lost'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_WON, 'Won'),
        (STATUS_LOST, 'Lost'),
    ]

    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.player.username} – {self.word.word} ({self.status})"

    @property
    def guess_count(self):
        return self.guesses.count()

    @property
    def is_complete(self):
        return self.status in (self.STATUS_WON, self.STATUS_LOST)

    class Meta:
        ordering = ['-started_at']


class Guess(models.Model):
    """A single guess attempt within a game."""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='guesses')
    attempt_number = models.PositiveSmallIntegerField()
    word = models.CharField(max_length=5)
    # result stored as JSON list e.g. ["green","grey","orange","grey","green"]
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Game {self.game_id} / Attempt {self.attempt_number}: {self.word}"

    class Meta:
        ordering = ['attempt_number']
        unique_together = [('game', 'attempt_number')]
