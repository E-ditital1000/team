from django.core.management.base import BaseCommand
from bloger.models import Category

class Command(BaseCommand):
    help = 'Populates the database with predefined categories'

    def handle(self, *args, **options):
        categories = {
            'Politics': 'politics',
            'Business': 'business',
            'Corporate': 'corporate',
            'Health': 'health',
            'Education': 'education',
            'Science': 'science',
            'Foods': 'foods',
            'Entertainment': 'entertainment',
            'Travel': 'travel',
            'Lifestyle': 'lifestyle'
        }

        for name, slug in categories.items():
            Category.objects.get_or_create(name=name, slug=slug)
            self.stdout.write(self.style.SUCCESS(f'Successfully added category: {name} with slug {slug}'))
