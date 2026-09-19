"""Preload the master list of enrichment item categories.

Transcribed from "Enrichment Calendars v4 - Item Categories List.pdf".

Run with: python3 manage.py import_item_categories
"""
from django.core.management.base import BaseCommand

from zoo.models import ItemCategory

CATEGORIES = [
    'Ball', 'Biological', 'Chew Toy', 'Fabric', 'Firehose', 'Food', 'General',
    'Hide', 'Kong', 'Puzzle feeder', 'PVC', 'Slow Feeder', 'Fasteners', 'Range',
]


class Command(BaseCommand):
    help = 'Preload the master list of enrichment item categories'

    def handle(self, *args, **options):
        created = 0
        for name in CATEGORIES:
            _, was_created = ItemCategory.objects.get_or_create(name=name)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f'Item categories: {created} created, {len(CATEGORIES) - created} already existed.'
        ))
