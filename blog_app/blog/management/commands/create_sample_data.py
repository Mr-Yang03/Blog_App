from django.core.management.base import BaseCommand
from blog.models import Category, Tag


class Command(BaseCommand):
    help = 'Creates sample categories and tags for the blog'

    def handle(self, *args, **kwargs):
        # Create categories
        categories_data = [
            {'name': 'Technology', 'description': 'Tech news and tutorials'},
            {'name': 'Programming', 'description': 'Programming languages and frameworks'},
            {'name': 'Web Development', 'description': 'Frontend and backend development'},
            {'name': 'Data Science', 'description': 'Data analysis and machine learning'},
            {'name': 'DevOps', 'description': 'DevOps practices and tools'},
            {'name': 'Mobile Development', 'description': 'iOS and Android development'},
            {'name': 'Design', 'description': 'UI/UX and graphic design'},
            {'name': 'Career', 'description': 'Career advice and job hunting'},
            {'name': 'Tutorial', 'description': 'Step-by-step tutorials'},
            {'name': 'News', 'description': 'Latest tech news'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        # Create tags
        tags_data = [
            'Python', 'JavaScript', 'Django', 'React', 'Node.js',
            'TypeScript', 'HTML', 'CSS', 'SQL', 'MongoDB',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'Git',
            'Machine Learning', 'AI', 'API', 'REST', 'GraphQL',
            'Testing', 'Security', 'Performance', 'Beginner', 'Advanced',
            'Tutorial', 'Best Practices', 'Tips', 'Guide', 'Review'
        ]

        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created tag: {tag.name}'))
            else:
                self.stdout.write(f'Tag already exists: {tag.name}')

        self.stdout.write(self.style.SUCCESS('\nSuccessfully created sample categories and tags!'))
