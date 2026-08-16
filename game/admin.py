from django.contrib import admin
from .models import Word, Game, Guess


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word',)
    search_fields = ('word',)
    ordering = ('word',)


class GuessInline(admin.TabularInline):
    model = Guess
    extra = 0
    readonly_fields = ('attempt_number', 'word', 'result', 'created_at')
    can_delete = False


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'word', 'status', 'guess_count', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('player__username', 'word__word')
    readonly_fields = ('started_at', 'completed_at')
    inlines = [GuessInline]

    def guess_count(self, obj):
        return obj.guesses.count()
    guess_count.short_description = 'Guesses'


@admin.register(Guess)
class GuessAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'attempt_number', 'word', 'result', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('game__player__username', 'word')
    readonly_fields = ('created_at',)
