"""
Forms for the game app.
"""
from django import forms
from django.contrib.auth.models import User
from .validators import validate_username, validate_password_strength


class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username (letters only, min 5)'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label='Confirm Password',
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        validate_username(username)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        validate_password_strength(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data


class GuessForm(forms.Form):
    guess = forms.CharField(
        max_length=5,
        min_length=5,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 5-letter word',
            'autocomplete': 'off',
            'class': 'guess-input',
            'maxlength': '5',
        }),
        label='',
    )

    def clean_guess(self):
        guess = self.cleaned_data.get('guess', '').strip().upper()
        if len(guess) != 5:
            raise forms.ValidationError('Guess must be exactly 5 letters.')
        if not guess.isalpha():
            raise forms.ValidationError('Guess must contain only letters.')
        return guess
