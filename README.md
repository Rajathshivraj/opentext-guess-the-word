# OpenText Guess the Word

A Wordle-style word-guessing game built with Django as the OpenText internship pre-boarding project.

---

## Project Overview

Players register, log in, and guess a secret 5-letter word. Each game allows up to **5 guesses**. Players may play **up to 3 games per day**. Letters are highlighted in **green** (correct position), **orange** (wrong position), or **grey** (not in word). Admins can manage the word list, inspect game data, and view analytical reports.

---

## Requirements Implemented

| Requirement | Implementation | Test |
|---|---|---|
| Two user types (Admin/Player) | Django `is_staff` flag | `test_player_cannot_access_daily_report` |
| Player registration | `RegistrationForm`, `register_view` | `test_valid_registration` |
| Login / Logout | `login_view`, `logout_view` | `test_successful_login` |
| Username ≥5 letters, alpha-only | `validate_username()` | `test_username_too_short` |
| Password ≥5 chars, alpha+digit+[$%*] | `validate_password_strength()` | `test_invalid_password_no_special` |
| 20 five-letter uppercase words | `seed_words` management command | `test_twenty_words_seeded` |
| Random word selection | `Word.objects.order_by('?').first()` | `test_new_game_created` |
| Max 3 games/day | Server-side date check in `new_game` view | `test_fourth_game_blocked` |
| 5-letter uppercase guesses | `GuessForm` validation | `test_invalid_guess_too_short` |
| Max 5 guesses/game | Attempt counter in `game_view` | `test_maximum_five_guesses_enforced` |
| Green/Orange/Grey evaluation | `evaluate_guess()` two-pass algorithm | `test_all_green`, `test_orange_*`, `test_grey_*` |
| Duplicate letter handling | Two-pass algorithm consumes letters | `test_guess_with_extra_duplicate_not_over_counted` |
| Win state | Status set to `won`, result modal shown | `test_winning_guess` |
| Loss state | 5 wrong guesses → `lost`, result modal | `test_losing_after_five_guesses` |
| Previous guesses retained | Saved `Guess` objects rendered in order | `test_previous_guesses_retained` |
| Secure password storage | Django `create_user()` (PBKDF2) | N/A (Django built-in) |
| CSRF protection | Django middleware enabled | N/A (framework) |
| Admin panel | `Word`, `Game`, `Guess` registered in admin | `test_admin_can_access_daily_report` |
| Daily report | `daily_report` view aggregates by date | `test_daily_report_correct_user_count` |
| User report | `user_report` view aggregates by player/date | `test_user_report_shows_correct_data` |

---

## Features

- 🔐 Secure registration with server-side validation
- 🎮 Wordle-style 5×5 guess grid with colour-coded tiles
- ⌨️ Virtual on-screen keyboard that tracks used letters
- 📅 3-games-per-day limit enforced server-side
- 🏆 Win/Loss result modal
- 📊 Admin reports: daily stats and per-user stats
- 👤 Player dashboard with today's games and history
- 🛡️ Authorization: players cannot access admin views
- 🧪 64 automated tests

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 6.0.7 |
| Database | SQLite (Django default) |
| Frontend | Django Templates, HTML5, CSS3, Vanilla JS |
| Auth | Django built-in User + authentication |
| Testing | Django TestCase |
| Version Control | Git + GitHub |

---

## Architecture

```
config/
    settings.py        ← project settings
    urls.py            ← root URL routing

game/
    models.py          ← Word, Game, Guess
    views.py           ← all views
    forms.py           ← RegistrationForm, GuessForm
    validators.py      ← username + password validators
    services.py        ← evaluate_guess() algorithm
    admin.py           ← admin registrations
    urls.py            ← game URL patterns
    tests.py           ← 64 automated tests

    templates/game/
        base.html
        home.html
        register.html
        login.html
        dashboard.html
        game.html
        reports/
            daily.html
            user.html

    static/game/
        css/style.css
        js/game.js

    management/commands/
        seed_words.py  ← idempotent word seeder
```

---

## Database Design

```
User (Django built-in)
  │
  │ 1-to-many
  ▼
Game
  ├── player (FK → User)
  ├── word   (FK → Word)
  ├── status (active / won / lost)
  ├── started_at
  └── completed_at
      │
      │ 1-to-many
      ▼
    Guess
      ├── game          (FK → Game)
      ├── attempt_number
      ├── word          (5-letter string)
      ├── result        (JSON: ["green","grey","orange","grey","green"])
      └── created_at

Word
  └── word (5-letter uppercase, unique)
```

---

## Setup Instructions

```powershell
# 1. Clone the repository
git clone https://github.com/Rajathshivraj/opentext-guess-the-word.git
cd opentext-guess-the-word

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Seed the word list
python manage.py seed_words

# 6. Create an admin account
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

---

## How to Play

1. Register at `/register/` — username must be ≥5 letters (alpha only); password must be ≥5 chars with at least one letter, number, and one of `$`, `%`, `*`.
2. Log in at `/login/`.
3. From the dashboard, click **Play New Game**.
4. Type a 5-letter word (or use the on-screen keyboard) and submit.
5. Colour cues guide your next guess:
   - 🟩 **Green** — right letter, right position
   - 🟧 **Orange** — right letter, wrong position
   - ⬛ **Grey** — letter not in word
6. Win by guessing the word within 5 attempts.
7. You may play up to **3 games per day**.

---

## Admin Reports

Log in to `/reports/daily/` or `/reports/user/` as an admin (staff) user.

- **Daily Report** — select a date to see number of players and correct guesses.
- **User Report** — select a player to see their per-day game and win counts.

The Django admin panel is available at `/admin/`.

---

## Testing

```powershell
python manage.py test game --verbosity=2
```

**64 tests** covering:
- Registration validation (username, password, duplicates)
- Authentication (login success/fail, logout)
- Word seeding (count, length, uppercase, idempotency)
- `evaluate_guess` (green, orange, grey, duplicate letters)
- Game flow (win, loss, 5-guess limit, previous guesses retained)
- Daily limit (1st–3rd game allowed, 4th blocked, cross-user independence, next-day reset)
- Authorization (player vs admin, unauthenticated access)
- Reports (daily report counts, user report data)

---

## Screenshots


---
<img width="1916" height="966" alt="Screenshot 2026-08-16 134535" src="https://github.com/user-attachments/assets/6816babd-4b07-4456-8a7a-15530098286c" />
<img width="1852" height="504" alt="Screenshot 2026-08-16 134709" src="https://github.com/user-attachments/assets/1b062357-114d-4694-97b4-0557c30c0c17" />
<img width="1907" height="890" alt="Screenshot 2026-08-16 212042" src="https://github.com/user-attachments/assets/ab677457-aadf-4d3d-81c5-a0622d961a70" />
<img width="1916" height="873" alt="Screenshot 2026-08-16 212128" src="https://github.com/user-attachments/assets/db882190-5ea0-440d-aee8-8bf316d8d4c9" />
<img width="1902" height="883" alt="Screenshot 2026-08-16 213235" src="https://github.com/user-attachments/assets/c45a7059-7023-4254-ac1c-297a8e0b4014" />
<img width="1902" height="838" alt="Screenshot 2026-08-16 213714" src="https://github.com/user-attachments/assets/d1dddf37-311f-4651-abee-4dd3751b65a6" />



## Requirement Traceability

All requirements from the OpenText project specification are implemented and traceable via the table in the **Requirements Implemented** section above. Each requirement maps to a view, model, or service function, and to a corresponding automated test.
