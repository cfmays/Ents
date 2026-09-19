"""Assign photos to Enrichment catalog items by matching filenames in a
source folder against item names.

Only ever applies EXACT or TIGHT (spacing-only-difference) normalized
matches -- never fuzzy guesses. This is deliberate: a wrong item/photo
association here is a real safety risk (e.g. the wrong ball size for an
animal), so anything short of an unambiguous name match is left for a
human to review by hand, never auto-assigned.

Idempotent: an item that already has a photo is left untouched, so this
is safe to re-run after adding more photos to the source folder.

Run with: python3 manage.py assign_enrichment_photos --source "/path/to/folder"
Add --dry-run to see what WOULD happen without writing anything.
"""
import os
import re

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from ents.models import Enrichment

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def normalize(s):
    s = re.sub(r'[^A-Za-z0-9]+', ' ', s)
    return s.strip().lower()


def tight(s):
    return normalize(s).replace(' ', '')


class Command(BaseCommand):
    help = 'Assign photos to Enrichment items by exact/tight filename-to-name match only (never fuzzy).'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True, help='Folder containing the photo files')
        parser.add_argument('--dry-run', action='store_true', help='Report what would happen without writing anything')

    def handle(self, *args, **options):
        source = options['source']
        dry_run = options['dry_run']
        if not os.path.isdir(source):
            raise CommandError(f'Not a directory: {source}')

        items = list(Enrichment.objects.all())
        item_by_key = {}
        item_by_tight = {}
        for item in items:
            item_by_key.setdefault(normalize(item.name), []).append(item)
            item_by_tight.setdefault(tight(item.name), []).append(item)

        assigned = 0
        skipped_has_photo = 0
        skipped_no_match = 0

        for fname in sorted(os.listdir(source)):
            base, ext = os.path.splitext(fname)
            if ext.lower() not in IMAGE_EXTENSIONS:
                continue

            candidates = item_by_key.get(normalize(base))
            if not candidates:
                candidates = item_by_tight.get(tight(base))
            if not candidates:
                skipped_no_match += 1
                continue

            full_path = os.path.join(source, fname)
            for item in candidates:
                if item.photo:
                    skipped_has_photo += 1
                    continue
                self.stdout.write(f'{fname}  ->  [{item.id}] {item.name}')
                if not dry_run:
                    with open(full_path, 'rb') as fh:
                        item.photo.save(fname, File(fh), save=True)
                assigned += 1

        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Assigned: {assigned}, skipped (already had a photo): {skipped_has_photo}, '
            f'skipped (no exact/tight match): {skipped_no_match}'
        ))
