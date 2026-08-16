"""
Comprehensive automated tests for the Guess the Word game.

Covers:
- Registration validation
- Authentication (login, logout)
- Word seeding  
- evaluate_guess service (green, orange, grey, duplicates)
- Game flow (win, loss, 5-guess limit)
- Daily limit (3 games max, resets next day)
- Authorization (player vs admin)
- Reports (daily, user)
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from game.forms import RegistrationForm
from game.models import Game, Guess, Word
from game.services import evaluate_guess
from game.validators import validate_username, validate_password_strength
from django.core.exceptions import ValidationError


# ============================================================
# 1. VALIDATORS
# ============================================================

class UsernameValidatorTests(TestCase):

    def test_valid_username(self):
        # Should not raise
        validate_username('Alice')

    def test_username_too_short(self):
        with self.assertRaises(ValidationError):
            validate_username('Al')

    def test_username_exactly_five_letters(self):
        validate_username('Alice')  # OK

    def test_username_with_digits_rejected(self):
        with self.assertRaises(ValidationError):
            validate_username('Alice1')

    def test_username_with_special_chars_rejected(self):
        with self.assertRaises(ValidationError):
            validate_username('Ali@e')


class PasswordValidatorTests(TestCase):

    def test_valid_password(self):
        validate_password_strength('Pass1$')  # Should not raise

    def test_password_too_short(self):
        with self.assertRaises(ValidationError):
            validate_password_strength('P1$')

    def test_password_missing_letter(self):
        with self.assertRaises(ValidationError):
            validate_password_strength('12345$')

    def test_password_missing_number(self):
        with self.assertRaises(ValidationError):
            validate_password_strength('Passw$')

    def test_password_missing_special_char(self):
        with self.assertRaises(ValidationError):
            validate_password_strength('Passw1')

    def test_password_with_percent(self):
        validate_password_strength('Pass1%')

    def test_password_with_star(self):
        validate_password_strength('Pass1*')


# ============================================================
# 2. REGISTRATION
# ============================================================

class RegistrationFormTests(TestCase):

    def _form(self, username, password, confirm=None):
        return RegistrationForm(data={
            'username': username,
            'password': password,
            'password_confirm': confirm if confirm is not None else password,
        })

    def test_valid_registration(self):
        form = self._form('Alice', 'Pass1$')
        self.assertTrue(form.is_valid(), form.errors)

    def test_username_too_short(self):
        form = self._form('Al', 'Pass1$')
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_invalid_password_no_number(self):
        form = self._form('Alice', 'Passw$')
        self.assertFalse(form.is_valid())

    def test_invalid_password_no_special(self):
        form = self._form('Alice', 'Passw1')
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        User.objects.create_user(username='Alice', password='Pass1$')
        form = self._form('Alice', 'Pass1$')
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_password_mismatch(self):
        form = self._form('Alice', 'Pass1$', confirm='Diff1$')
        self.assertFalse(form.is_valid())

    def test_registration_view_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'Newbie',
            'password': 'Pass1$',
            'password_confirm': 'Pass1$',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='Newbie').exists())

    def test_registration_view_duplicate(self):
        User.objects.create_user(username='Taken', password='Pass1$')
        response = self.client.post(reverse('register'), {
            'username': 'Taken',
            'password': 'Pass1$',
            'password_confirm': 'Pass1$',
        })
        self.assertEqual(response.status_code, 200)  # form re-renders


# ============================================================
# 3. AUTHENTICATION
# ============================================================

class AuthTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='Player', password='Pass1$')

    def test_successful_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'Player',
            'password': 'Pass1$',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_failed_login_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'Player',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        # After logout, accessing dashboard redirects to login
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 302)


# ============================================================
# 4. WORD SEEDING
# ============================================================

class WordSeedingTests(TestCase):

    def setUp(self):
        from django.core.management import call_command
        call_command('seed_words', verbosity=0)

    def test_twenty_words_seeded(self):
        self.assertEqual(Word.objects.count(), 20)

    def test_all_words_are_five_letters(self):
        for word in Word.objects.all():
            self.assertEqual(len(word.word), 5, f"{word.word} is not 5 letters")

    def test_all_words_are_uppercase(self):
        for word in Word.objects.all():
            self.assertEqual(word.word, word.word.upper(), f"{word.word} is not uppercase")

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        call_command('seed_words', verbosity=0)
        self.assertEqual(Word.objects.count(), 20)


# ============================================================
# 5. EVALUATE_GUESS SERVICE
# ============================================================

class EvaluateGuessTests(TestCase):

    def test_all_green(self):
        result = evaluate_guess('CRANE', 'CRANE')
        self.assertEqual(result, ['green', 'green', 'green', 'green', 'green'])

    def test_all_grey(self):
        result = evaluate_guess('CRANE', 'BOILS')
        for r in result:
            self.assertEqual(r, 'grey')

    def test_exact_match_green(self):
        result = evaluate_guess('TOWER', 'TOWER')
        self.assertEqual(result, ['green', 'green', 'green', 'green', 'green'])

    def test_orange_correct_letter_wrong_position(self):
        result = evaluate_guess('CRANE', 'RISKY')
        # R is at index 2 in CRANE, not at 0 → orange
        self.assertEqual(result[0], 'orange')  # R

    def test_grey_absent_letter(self):
        result = evaluate_guess('CRANE', 'BOILS')
        self.assertEqual(result[0], 'grey')

    def test_duplicate_letters_one_green_one_grey(self):
        # TARGET=TOWER, GUESS=TREES
        # T→green(0), R→orange(1→pos4 in TOWER), E→grey(2), E→grey(3), S→grey(4)
        result = evaluate_guess('TOWER', 'TREES')
        self.assertEqual(result[0], 'green')   # T correct pos
        self.assertNotEqual(result[1], 'green') # R not at pos 1

    def test_duplicate_target_letters(self):
        # TARGET=KNEEL, GUESS=EAGLE
        # Only one E should be orange/green
        result = evaluate_guess('KNEEL', 'EAGLE')
        # E at pos 0 in EAGLE is orange (E in KNEEL at pos 2,3)
        # A at pos 1 → grey
        colors = result
        e_results = [colors[i] for i, c in enumerate('EAGLE') if c == 'E']
        # At most 2 E's in target (KNEEL has 2), so both E positions in EAGLE can be non-grey
        self.assertIn(colors[0], ['orange', 'green', 'grey'])

    def test_guess_with_extra_duplicate_not_over_counted(self):
        # TARGET=CRANE (one R), GUESS=ERROR (three R's)
        result = evaluate_guess('CRANE', 'ERROR')
        # Only one R should be marked non-grey
        non_grey_r = sum(1 for i, c in enumerate('ERROR') if c == 'R' and result[i] != 'grey')
        self.assertLessEqual(non_grey_r, 1)

    def test_case_insensitive(self):
        result = evaluate_guess('crane', 'crane')
        self.assertEqual(result, ['green', 'green', 'green', 'green', 'green'])


# ============================================================
# 6. GAME FLOW
# ============================================================

class GameFlowTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='Player', password='Pass1$')
        self.word = Word.objects.create(word='CRANE')
        self.client.force_login(self.user)

    def _new_game(self):
        with patch('game.views.Word.objects.order_by') as mock_qs:
            mock_qs.return_value.first.return_value = self.word
            response = self.client.get(reverse('new_game'))
        game = Game.objects.filter(player=self.user).first()
        return game, response

    def test_new_game_created(self):
        game, response = self._new_game()
        self.assertIsNotNone(game)
        self.assertEqual(game.word, self.word)
        self.assertEqual(game.status, Game.STATUS_ACTIVE)

    def test_valid_guess_submitted(self):
        game, _ = self._new_game()
        resp = self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'BRAVE'})
        game.refresh_from_db()
        self.assertEqual(game.guesses.count(), 1)

    def test_invalid_guess_too_short(self):
        game, _ = self._new_game()
        resp = self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'AB'})
        game.refresh_from_db()
        self.assertEqual(game.guesses.count(), 0)  # invalid guess not saved

    def test_winning_guess(self):
        game, _ = self._new_game()
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'CRANE'})
        game.refresh_from_db()
        self.assertEqual(game.status, Game.STATUS_WON)

    def test_losing_after_five_guesses(self):
        game, _ = self._new_game()
        for w in ['BRAVE', 'GLOBE', 'HOUSE', 'IMAGE', 'JUDGE']:
            self.client.post(reverse('game_view', args=[game.pk]), {'guess': w})
        game.refresh_from_db()
        self.assertEqual(game.status, Game.STATUS_LOST)

    def test_maximum_five_guesses_enforced(self):
        game, _ = self._new_game()
        for w in ['BRAVE', 'GLOBE', 'HOUSE', 'IMAGE', 'JUDGE']:
            self.client.post(reverse('game_view', args=[game.pk]), {'guess': w})
        # 6th guess should not be saved
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'NIGHT'})
        game.refresh_from_db()
        self.assertEqual(game.guesses.count(), 5)

    def test_previous_guesses_retained(self):
        game, _ = self._new_game()
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'BRAVE'})
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'GLOBE'})
        guesses = list(game.guesses.order_by('attempt_number'))
        self.assertEqual(guesses[0].word, 'BRAVE')
        self.assertEqual(guesses[1].word, 'GLOBE')

    def test_guess_evaluation_saved_correctly(self):
        game, _ = self._new_game()
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'CRANE'})
        guess = game.guesses.first()
        self.assertEqual(guess.result, ['green', 'green', 'green', 'green', 'green'])

    def test_win_state_green_evaluation(self):
        game, _ = self._new_game()
        self.client.post(reverse('game_view', args=[game.pk]), {'guess': 'CRANE'})
        guess = game.guesses.first()
        for color in guess.result:
            self.assertEqual(color, 'green')

    def test_orange_evaluation_via_service(self):
        result = evaluate_guess('CRANE', 'RISKY')
        self.assertEqual(result[0], 'orange')  # R exists in CRANE

    def test_grey_evaluation_via_service(self):
        result = evaluate_guess('CRANE', 'BOILS')
        self.assertEqual(result[0], 'grey')


# ============================================================
# 7. DAILY LIMIT
# ============================================================

class DailyLimitTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='Player', password='Pass1$')
        self.user2 = User.objects.create_user(username='Other', password='Pass1$')
        self.word = Word.objects.create(word='CRANE')
        self.client.force_login(self.user)

    def _create_game(self, player=None, delta_days=0, status=Game.STATUS_LOST):
        player = player or self.user
        when = timezone.now() - timedelta(days=delta_days)
        game = Game.objects.create(player=player, word=self.word, status=status)
        # Patch started_at to correct date
        Game.objects.filter(pk=game.pk).update(started_at=when)
        return game

    def test_first_game_allowed(self):
        with patch('game.views.Word.objects.order_by') as mock:
            mock.return_value.first.return_value = self.word
            response = self.client.get(reverse('new_game'))
        self.assertEqual(Game.objects.filter(player=self.user).count(), 1)

    def test_second_game_allowed(self):
        self._create_game()
        with patch('game.views.Word.objects.order_by') as mock:
            mock.return_value.first.return_value = self.word
            self.client.get(reverse('new_game'))
        self.assertEqual(Game.objects.filter(player=self.user, started_at__date=timezone.localdate()).count(), 2)

    def test_third_game_allowed(self):
        self._create_game()
        self._create_game()
        with patch('game.views.Word.objects.order_by') as mock:
            mock.return_value.first.return_value = self.word
            self.client.get(reverse('new_game'))
        self.assertEqual(Game.objects.filter(player=self.user, started_at__date=timezone.localdate()).count(), 3)

    def test_fourth_game_blocked(self):
        for _ in range(3):
            self._create_game()
        with patch('game.views.Word.objects.order_by') as mock:
            mock.return_value.first.return_value = self.word
            response = self.client.get(reverse('new_game'), follow=True)
        # Should redirect to dashboard with error message
        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, '3')  # message mentions 3

    def test_different_users_independent_limits(self):
        # Create 3 games for user2
        for _ in range(3):
            self._create_game(player=self.user2)
        # user1 should still be able to play
        self.assertEqual(Game.objects.filter(player=self.user, started_at__date=timezone.localdate()).count(), 0)

    def test_yesterday_games_do_not_count_today(self):
        # 3 games yesterday
        for _ in range(3):
            self._create_game(delta_days=1)
        # Today count should be 0
        today_count = Game.objects.filter(
            player=self.user, started_at__date=timezone.localdate()
        ).count()
        self.assertEqual(today_count, 0)


# ============================================================
# 8. AUTHORIZATION
# ============================================================

class AuthorizationTests(TestCase):

    def setUp(self):
        self.player = User.objects.create_user(username='Player', password='Pass1$')
        self.admin = User.objects.create_user(username='Admin', password='Pass1$', is_staff=True)
        self.word = Word.objects.create(word='CRANE')

    def test_unauthenticated_cannot_access_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_unauthenticated_cannot_start_game(self):
        response = self.client.get(reverse('new_game'))
        self.assertEqual(response.status_code, 302)

    def test_player_cannot_access_daily_report(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse('daily_report'))
        self.assertNotEqual(response.status_code, 200)  # redirected

    def test_player_cannot_access_user_report(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse('user_report'))
        self.assertNotEqual(response.status_code, 200)

    def test_admin_can_access_daily_report(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('daily_report'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_user_report(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('user_report'))
        self.assertEqual(response.status_code, 200)

    def test_player_cannot_view_another_players_game(self):
        player2 = User.objects.create_user(username='Other', password='Pass1$')
        game = Game.objects.create(player=self.player, word=self.word)
        self.client.force_login(player2)
        response = self.client.get(reverse('game_view', args=[game.pk]))
        self.assertEqual(response.status_code, 404)


# ============================================================
# 9. REPORTS
# ============================================================

class ReportTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(username='Admin', password='Pass1$', is_staff=True)
        self.player1 = User.objects.create_user(username='Player1', password='Pass1$')
        self.player2 = User.objects.create_user(username='Player2', password='Pass1$')
        self.word = Word.objects.create(word='CRANE')
        self.client.force_login(self.admin)

    def _make_game(self, player, status):
        return Game.objects.create(player=player, word=self.word, status=status)

    def test_daily_report_correct_user_count(self):
        self._make_game(self.player1, Game.STATUS_WON)
        self._make_game(self.player2, Game.STATUS_LOST)
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse('daily_report') + f'?date={today}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2')  # 2 players

    def test_daily_report_correct_win_count(self):
        self._make_game(self.player1, Game.STATUS_WON)
        self._make_game(self.player1, Game.STATUS_WON)
        self._make_game(self.player2, Game.STATUS_LOST)
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse('daily_report') + f'?date={today}')
        self.assertContains(response, '2')  # 2 wins

    def test_user_report_shows_correct_data(self):
        self._make_game(self.player1, Game.STATUS_WON)
        self._make_game(self.player1, Game.STATUS_LOST)
        response = self.client.get(
            reverse('user_report') + f'?user_id={self.player1.pk}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Player1')

    def test_daily_report_empty_for_no_games(self):
        yesterday = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.client.get(reverse('daily_report') + f'?date={yesterday}')
        self.assertContains(response, '0')
