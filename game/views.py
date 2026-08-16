"""
Views for the Guess the Word game.
"""
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from .models import Word, Game, Guess
from .forms import RegistrationForm, GuessForm
from .services import evaluate_guess


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_admin(user):
    """Return True if user is staff/superuser."""
    return user.is_authenticated and user.is_staff


def _games_today(user):
    """Return queryset of today's games for user."""
    today = timezone.localdate()
    return Game.objects.filter(
        player=user,
        started_at__date=today,
    )


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------

def home(request):
    """Landing page."""
    return render(request, 'game/home.html')


def register_view(request):
    """Player registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'game/register.html', {'form': form})


def login_view(request):
    """Player login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'game/login.html')


def logout_view(request):
    """Logout (POST only for CSRF safety)."""
    if request.method == 'POST':
        logout(request)
    return redirect('home')


# ---------------------------------------------------------------------------
# Player views (login required)
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Player dashboard — shows today's game count and history."""
    today = timezone.localdate()
    today_games = _games_today(request.user).order_by('-started_at')
    games_remaining = max(0, 3 - today_games.count())

    past_games = Game.objects.filter(
        player=request.user,
    ).exclude(
        started_at__date=today,
    ).order_by('-started_at')[:10]

    context = {
        'today_games': today_games,
        'past_games': past_games,
        'games_remaining': games_remaining,
        'today': today,
    }
    return render(request, 'game/dashboard.html', context)


@login_required
def new_game(request):
    """Start a new game (enforces 3-per-day limit)."""
    today_count = _games_today(request.user).count()

    if today_count >= 3:
        messages.error(
            request,
            "You've already played 3 games today. Come back tomorrow!"
        )
        return redirect('dashboard')

    # Check for an already-active game today
    active = _games_today(request.user).filter(status=Game.STATUS_ACTIVE).first()
    if active:
        return redirect('game_view', pk=active.pk)

    # Pick a random word
    word_count = Word.objects.count()
    if word_count == 0:
        messages.error(request, "No words available. Please contact the administrator.")
        return redirect('dashboard')

    word = Word.objects.order_by('?').first()
    game = Game.objects.create(player=request.user, word=word)

    return redirect('game_view', pk=game.pk)


@login_required
def game_view(request, pk):
    """Active game view — handles guess submission."""
    game = get_object_or_404(Game, pk=pk, player=request.user)
    guesses = game.guesses.all().order_by('attempt_number')
    form = GuessForm()
    show_result = None

    if game.is_complete and request.method == 'GET':
        # Game is already done — show result
        show_result = game.status

    if not game.is_complete and request.method == 'POST':
        form = GuessForm(request.POST)
        if form.is_valid():
            guess_word = form.cleaned_data['guess']
            attempt = guesses.count() + 1

            if attempt > 5:
                messages.error(request, 'No more guesses allowed.')
            else:
                result = evaluate_guess(game.word.word, guess_word)
                Guess.objects.create(
                    game=game,
                    attempt_number=attempt,
                    word=guess_word,
                    result=result,
                )

                if guess_word == game.word.word:
                    game.status = Game.STATUS_WON
                    game.completed_at = timezone.now()
                    game.save()
                    show_result = 'won'
                elif attempt >= 5:
                    game.status = Game.STATUS_LOST
                    game.completed_at = timezone.now()
                    game.save()
                    show_result = 'lost'

                # Refresh guesses after saving
                guesses = game.guesses.all().order_by('attempt_number')

    # Build grid rows (up to 5)
    grid_rows = []
    for g in guesses:
        row = [
            {'letter': g.word[i], 'color': g.result[i]}
            for i in range(5)
        ]
        grid_rows.append(row)

    # Add empty rows for remaining guesses
    empty_rows_count = 5 - len(grid_rows)

    guesses_used = guesses.count()
    guesses_left = max(0, 5 - guesses_used)

    today_count = _games_today(request.user).count()
    games_remaining = max(0, 3 - today_count)

    context = {
        'game': game,
        'grid_rows': grid_rows,
        'empty_rows_count': empty_rows_count,
        'form': form,
        'guesses_used': guesses_used,
        'guesses_left': guesses_left,
        'games_remaining': games_remaining,
        'show_result': show_result,
        'target_word': game.word.word if game.is_complete else None,
    }
    return render(request, 'game/game.html', context)


# ---------------------------------------------------------------------------
# Admin / Staff only views
# ---------------------------------------------------------------------------

@user_passes_test(_is_admin, login_url='/login/')
def daily_report(request):
    """Admin daily report — select date, view users + correct guesses."""
    from datetime import date

    report_date = None
    num_users = None
    num_wins = None

    if request.method == 'GET' and 'date' in request.GET:
        date_str = request.GET.get('date', '')
        try:
            year, month, day = map(int, date_str.split('-'))
            report_date = date(year, month, day)
            games_on_date = Game.objects.filter(started_at__date=report_date)
            num_users = games_on_date.values('player').distinct().count()
            num_wins = games_on_date.filter(status=Game.STATUS_WON).count()
        except (ValueError, AttributeError):
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')

    context = {
        'report_date': report_date,
        'num_users': num_users,
        'num_wins': num_wins,
        'today': timezone.localdate(),
    }
    return render(request, 'game/reports/daily.html', context)


@user_passes_test(_is_admin, login_url='/login/')
def user_report(request):
    """Admin user report — select player, view per-day stats."""
    players = User.objects.filter(is_staff=False).order_by('username')
    selected_user = None
    report_rows = []

    if request.method == 'GET' and 'user_id' in request.GET:
        user_id = request.GET.get('user_id')
        try:
            selected_user = User.objects.get(pk=user_id)
            # Aggregate games grouped by date
            from django.db.models.functions import TruncDate
            rows = (
                Game.objects.filter(player=selected_user)
                .annotate(date=TruncDate('started_at'))
                .values('date')
                .annotate(
                    words_tried=Count('id'),
                    correct_guesses=Count('id', filter=Q(status=Game.STATUS_WON)),
                )
                .order_by('-date')
            )
            report_rows = list(rows)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')

    context = {
        'players': players,
        'selected_user': selected_user,
        'report_rows': report_rows,
    }
    return render(request, 'game/reports/user.html', context)
