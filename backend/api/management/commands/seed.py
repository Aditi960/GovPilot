from django.core.management.base import BaseCommand
from api.models import User, Role, GovernmentDepartment, Startup, Challenge, ChallengeStatus
import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed database with initial data for demo'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create Users
        admin, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@sih.gov.in', 'role': Role.ADMIN})
        admin.set_password('admin')
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

        gov_user, _ = User.objects.get_or_create(username='gov_officer', defaults={'email': 'officer@moud.gov.in', 'role': Role.GOVERNMENT})
        gov_user.set_password('password')
        gov_user.save()

        expert_user, _ = User.objects.get_or_create(username='expert_1', defaults={'email': 'expert@academia.edu', 'role': Role.EXPERT})
        expert_user.set_password('password')
        expert_user.save()

        startup_user, _ = User.objects.get_or_create(username='startup_1', defaults={'email': 'founder@ecoai.tech', 'role': Role.STARTUP})
        startup_user.set_password('password')
        startup_user.save()

        # Create Department
        dept, _ = GovernmentDepartment.objects.get_or_create(name='Department of Urban Development', defaults={'officer': gov_user})

        # Create Startup Profile
        startup, _ = Startup.objects.get_or_create(user=startup_user, defaults={
            'name': 'EcoAI Technologies',
            'registration_number': 'REG-2026-001',
            'dpiit_number': 'DIPP12345',
            'founded_year': 2024
        })

        # Create Challenge
        Challenge.objects.get_or_create(
            challenge_id='CHL-2026-001',
            defaults={
                'title': 'AI-based Waste Segregation Monitoring',
                'department': dept,
                'category': 'Waste Management',
                'problem_statement': 'Inefficient manual waste segregation leading to landfill overflow.',
                'desired_outcome': 'Automated monitoring to achieve 90% accuracy in segregation.',
                'budget': 1000000.00,
                'pilot_duration': 90,
                'status': ChallengeStatus.PUBLISHED,
                'application_deadline': timezone.now() + datetime.timedelta(days=30)
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database.'))
