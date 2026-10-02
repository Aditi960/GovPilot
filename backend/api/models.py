import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.TextChoices):
    GOVERNMENT = 'GOVERNMENT', 'Government'
    STARTUP = 'STARTUP', 'Startup'
    EXPERT = 'EXPERT', 'Expert'
    ADMIN = 'ADMIN', 'Admin'

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STARTUP)
    
    # We will use email as the primary identifier instead of username if desired, 
    # but for simplicity we keep AbstractUser defaults and just ensure email is unique if needed.

class GovernmentDepartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='departments')

    def __str__(self):
        return self.name

class Startup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='startup_profile')
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True)
    dpiit_number = models.CharField(max_length=100, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    headquarters = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class StartupTeamMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    experience = models.TextField(blank=True)

class ChallengeStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    APPLICATIONS_OPEN = 'APPLICATIONS_OPEN', 'Applications Open'
    APPLICATIONS_CLOSED = 'APPLICATIONS_CLOSED', 'Applications Closed'
    EVALUATION = 'EVALUATION', 'Evaluation'
    SELECTION = 'SELECTION', 'Selection'
    COMPLETED = 'COMPLETED', 'Completed'

class Challenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    department = models.ForeignKey(GovernmentDepartment, on_delete=models.CASCADE, related_name='challenges')
    category = models.CharField(max_length=100)
    problem_statement = models.TextField()
    desired_outcome = models.TextField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    pilot_duration = models.IntegerField(help_text="Duration in days")
    status = models.CharField(max_length=30, choices=ChallengeStatus.choices, default=ChallengeStatus.DRAFT)
    application_deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ChallengeEligibility(models.Model):
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='eligibility')
    requires_dpiit = models.BooleanField(default=True)
    required_certifications = models.TextField(blank=True)

class ChallengeEvaluationCriteria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='evaluation_criteria')
    name = models.CharField(max_length=255)
    weight_percentage = models.IntegerField()

class ApplicationStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    ELIGIBILITY_REVIEW = 'ELIGIBILITY_REVIEW', 'Eligibility Review'
    ELIGIBLE = 'ELIGIBLE', 'Eligible'
    INELIGIBLE = 'INELIGIBLE', 'Ineligible'
    UNDER_EVALUATION = 'UNDER_EVALUATION', 'Under Evaluation'
    SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
    SELECTED = 'SELECTED', 'Selected'
    REJECTED = 'REJECTED', 'Rejected'

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='applications')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='applications')
    solution_title = models.CharField(max_length=255)
    solution_description = models.TextField()
    status = models.CharField(max_length=30, choices=ApplicationStatus.choices, default=ApplicationStatus.DRAFT)
    eligibility_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DocumentType(models.TextChoices):
    TECHNICAL_PROPOSAL = 'TECHNICAL_PROPOSAL', 'Technical Proposal'
    REGISTRATION = 'REGISTRATION', 'Registration'
    DPIIT = 'DPIIT', 'DPIIT'
    OTHER = 'OTHER', 'Other'

class ApplicationDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to='application_docs/')

class ExpertAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='expert_assignments')
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_applications')
    has_conflict_of_interest = models.BooleanField(default=False)

class Evaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(ExpertAssignment, on_delete=models.CASCADE, related_name='evaluation')
    criteria_scores = models.JSONField(default=dict)
    comments = models.TextField(blank=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

class PilotStatus(models.TextChoices):
    PLANNED = 'PLANNED', 'Planned'
    ACTIVE = 'ACTIVE', 'Active'
    COMPLETED = 'COMPLETED', 'Completed'
    VALIDATED = 'VALIDATED', 'Validated'
    SCALE_UP = 'SCALE_UP', 'Scale Up'
    CLOSED = 'CLOSED', 'Closed'

class Pilot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='pilot')
    title = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PilotStatus.choices, default=PilotStatus.PLANNED)
    success_criteria = models.TextField(blank=True)

class MilestoneStatus(models.TextChoices):
    NOT_STARTED = 'NOT_STARTED', 'Not Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'
    PAID = 'PAID', 'Paid'

class PilotMilestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    kpi_name = models.CharField(max_length=255)
    target_value = models.CharField(max_length=255)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=MilestoneStatus.choices, default=MilestoneStatus.NOT_STARTED)

class MilestoneSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    milestone = models.OneToOneField(PilotMilestone, on_delete=models.CASCADE, related_name='submission')
    actual_kpi_result = models.CharField(max_length=255)
    description = models.TextField()
    evidence_files = models.JSONField(default=list)

class ValidationStatus(models.TextChoices):
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'
    REQUEST_CORRECTION = 'REQUEST_CORRECTION', 'Request Correction'

class Validation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(MilestoneSubmission, on_delete=models.CASCADE, related_name='validation')
    expert = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ValidationStatus.choices)
    comments = models.TextField(blank=True)

class PaymentStatus(models.TextChoices):
    LOCKED = 'LOCKED', 'Locked'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    RELEASED = 'RELEASED', 'Released'

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.CharField(max_length=100, unique=True)
    milestone = models.OneToOneField(PilotMilestone, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.LOCKED)
    simulated_transaction_id = models.CharField(max_length=100, blank=True)

class ScaleUpDecisionStatus(models.TextChoices):
    SCALE_UP = 'SCALE_UP', 'Scale Up'
    CLOSE = 'CLOSE', 'Close'

class ScaleUpDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot = models.OneToOneField(Pilot, on_delete=models.CASCADE, related_name='scale_up_decision')
    decision = models.CharField(max_length=20, choices=ScaleUpDecisionStatus.choices)
    reason = models.TextField()
    approved_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    previous_state = models.CharField(max_length=255, blank=True)
    new_state = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
