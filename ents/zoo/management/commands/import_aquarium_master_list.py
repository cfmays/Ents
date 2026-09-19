"""
Add the aquarium items ("Master List Template" sheet of the aquarium workbook) to the master item list.

Same name (ignoring extra spaces and upper/lower case) = same item: existing items are left alone,
including their category and photo. (The aquarium sheet mostly says 'General', so only other differing categories are reported.) Only new names are created (no photo yet).
Items whose category is still the placeholder 'Unknown' take the aquarium sheet's category.

  python3 manage.py import_aquarium_master_list "../Aquarium Enrichment Calendars V4.xlsx" --dry-run
"""
import re

import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction

from ents.models import Enrichment
from zoo.models import ItemCategory


def clean(value):
    return re.sub(r'\s+', ' ', str(value)).strip() if value is not None else ''


class Command(BaseCommand):
    help = 'Add new aquarium items from the aquarium workbook to the master list'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path')
        parser.add_argument('--dry-run', action='store_true', help='Do everything, then roll back.')
        parser.add_argument('--report', default='aquarium_master_report.txt')

    def handle(self, *args, **options):
        ws = openpyxl.load_workbook(options['xlsx_path'], data_only=True)['Master List Template']
        existing = {clean(e.name).lower(): e for e in Enrichment.objects.select_related('category')}
        report = []
        created = 0
        already = 0
        filled = 0
        with transaction.atomic():
            for row in range(2, ws.max_row + 1):
                name = clean(ws.cell(row, 1).value)
                category_name = clean(ws.cell(row, 2).value) or 'Unknown'
                if not name:
                    continue
                item = existing.get(name.lower())
                if item is not None:
                    already += 1
                    if item.category and item.category.name == 'Unknown' and category_name not in ('General', 'Unknown'):
                        item.category, _ = ItemCategory.objects.get_or_create(name=category_name)
                        item.save()
                        filled += 1
                    elif item.category and item.category.name != category_name and category_name != 'General':
                        report.append(
                            f'CATEGORY DIFFERS (kept "{item.category.name}", aquarium sheet says '
                            f'"{category_name}"): {name}'
                        )
                    continue
                category, _ = ItemCategory.objects.get_or_create(name=category_name)
                existing[name.lower()] = Enrichment.objects.create(name=name, category=category)
                created += 1
            if options['dry_run']:
                transaction.set_rollback(True)

        with open(options['report'], 'w') as f:
            f.write('\n'.join(report) + '\n')
        self.stdout.write(self.style.SUCCESS(
            f'{"DRY RUN (rolled back): " if options["dry_run"] else ""}{created} items created, {already} names already '
            f'in the master list ({filled} of them had category Unknown, now filled in from the aquarium sheet; {len(report)} with a different category; see {options["report"]}).'
        ))
