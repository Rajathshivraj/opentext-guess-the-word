"""
Management command to seed 20 five-letter uppercase words into the database.
Running multiple times is idempotent (no duplicates created).
"""
from django.core.management.base import BaseCommand
from game.models import Word


WORDS = [
    'CRANE', 'PLANT', 'STONE', 'BRAVE', 'FLAME',
    'GLOBE', 'HOUSE', 'IMAGE', 'JUDGE', 'KNIFE',
    'LIGHT', 'MONEY', 'NIGHT', 'OCEAN', 'POWER',
    'QUEEN', 'RIVER', 'SHIRT', 'TIGER', 'ULTRA',
]


class Command(BaseCommand):
    help = 'Seed the database with 20 five-letter words for the game.'

    def handle(self, *args, **options):
        created_count = 0
        for word_str in WORDS:
            _, created = Word.objects.get_or_create(word=word_str.upper())
            if created:
                created_count += 1

        if created_count:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully seeded {created_count} new word(s).')
            )
        else:
            self.stdout.write(
                self.style.WARNING('All words already exist. Nothing to seed.')
            )
