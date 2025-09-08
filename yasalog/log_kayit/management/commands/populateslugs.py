from django.core.management.base import BaseCommand
from django.utils.text import slugify
from log_kayit.models import Company

class Command(BaseCommand):
    help = 'Ensures all existing Company objects have a unique slug.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate slugs for companies...'))
        
        companies = Company.objects.all()
        updated_count = 0
        
        for company in companies:
            if not company.slug:
                base_slug = slugify(company.name)
                slug = base_slug
                counter = 1
                
                # Slug'ın benzersiz olduğundan emin ol
                while Company.objects.filter(slug=slug).exclude(id=company.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                company.slug = slug
                company.save(update_fields=['slug'])
                self.stdout.write(self.style.SUCCESS(f'Successfully created slug for "{company.name}": {company.slug}'))
                updated_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'Skipping "{company.name}", already has slug: {company.slug}'))
                
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\nFinished. Successfully updated {updated_count} companies.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nFinished. No companies needed an update.')) 