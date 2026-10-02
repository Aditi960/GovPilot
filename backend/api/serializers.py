from rest_framework import serializers
from .models import (
    User, GovernmentDepartment, Challenge, ChallengeEligibility, 
    ChallengeEvaluationCriteria, Startup, Application, Pilot,
    PilotMilestone, MilestoneSubmission, Validation, Payment, ScaleUpDecision, StartupTeamMember,
    Application, ApplicationDocument, ExpertAssignment, Evaluation
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']

class StartupTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupTeamMember
        fields = ['id', 'name', 'role', 'experience']

class StartupSerializer(serializers.ModelSerializer):
    team_members = StartupTeamMemberSerializer(many=True, required=False)

    class Meta:
        model = Startup
        fields = [
            'id', 'name', 'registration_number', 'dpiit_number',
            'founded_year', 'headquarters', 'website', 'team_members'
        ]

    def create(self, validated_data):
        team_data = validated_data.pop('team_members', [])
        startup = Startup.objects.create(**validated_data)
        for member in team_data:
            StartupTeamMember.objects.create(startup=startup, **member)
        return startup

    def update(self, instance, validated_data):
        team_data = validated_data.pop('team_members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if team_data is not None:
            instance.team_members.all().delete()
            for member in team_data:
                StartupTeamMember.objects.create(startup=instance, **member)
        return instance

class GovernmentDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentDepartment
        fields = '__all__'

class ChallengeEligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeEligibility
        fields = ['requires_dpiit', 'required_certifications']

class ChallengeEvaluationCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeEvaluationCriteria
        fields = ['id', 'name', 'weight_percentage']

class ChallengeSerializer(serializers.ModelSerializer):
    eligibility = ChallengeEligibilitySerializer(required=False)
    evaluation_criteria = ChallengeEvaluationCriteriaSerializer(many=True, required=False)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Challenge
        fields = [
            'id', 'challenge_id', 'title', 'department', 'department_name', 'category', 
            'problem_statement', 'desired_outcome', 'budget', 'pilot_duration', 
            'status', 'application_deadline', 'created_at', 'eligibility', 'evaluation_criteria'
        ]

    def create(self, validated_data):
        eligibility_data = validated_data.pop('eligibility', None)
        criteria_data = validated_data.pop('evaluation_criteria', [])
        
        challenge = Challenge.objects.create(**validated_data)
        
        if eligibility_data:
            ChallengeEligibility.objects.create(challenge=challenge, **eligibility_data)
            
        for criterion in criteria_data:
            ChallengeEvaluationCriteria.objects.create(challenge=challenge, **criterion)
            
        return challenge

    def update(self, instance, validated_data):
        eligibility_data = validated_data.pop('eligibility', None)
        criteria_data = validated_data.pop('evaluation_criteria', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if eligibility_data is not None:
            eligibility, created = ChallengeEligibility.objects.get_or_create(challenge=instance)
            for attr, value in eligibility_data.items():
                setattr(eligibility, attr, value)
            eligibility.save()

        if criteria_data is not None:
            instance.evaluation_criteria.all().delete()
            for criterion in criteria_data:
                ChallengeEvaluationCriteria.objects.create(challenge=instance, **criterion)

        return instance

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ['id', 'document_type', 'file']

class ApplicationSerializer(serializers.ModelSerializer):
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    startup_name = serializers.CharField(source='startup.name', read_only=True)
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'challenge', 'challenge_title', 'startup', 'startup_name',
            'solution_title', 'solution_description', 'status',
            'eligibility_notes', 'created_at', 'documents'
        ]
        read_only_fields = ['status', 'startup', 'eligibility_notes']

    def create(self, validated_data):
        # We will attach the startup from request.user in the view
        return Application.objects.create(**validated_data)

class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['id', 'assignment', 'criteria_scores', 'comments', 'final_score']
        read_only_fields = ['final_score']

class ExpertAssignmentSerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(source='expert.username', read_only=True)
    evaluation = EvaluationSerializer(read_only=True)
    
    # We might want some application info for the expert to see
    application_title = serializers.CharField(source='application.solution_title', read_only=True)
    challenge_title = serializers.CharField(source='application.challenge.title', read_only=True)

    class Meta:
        model = ExpertAssignment
        fields = [
            'id', 'application', 'application_title', 'challenge_title',
            'expert', 'expert_name', 'has_conflict_of_interest', 'evaluation'
        ]

class PilotMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilotMilestone
        fields = ['id', 'pilot', 'name', 'description', 'due_date', 'kpi_name', 'target_value', 'payment_amount', 'status']
        read_only_fields = ['status']

class PilotSerializer(serializers.ModelSerializer):
    milestones = PilotMilestoneSerializer(many=True, read_only=True)
    application_title = serializers.CharField(source='application.solution_title', read_only=True)
    challenge_title = serializers.CharField(source='application.challenge.title', read_only=True)
    startup_name = serializers.CharField(source='application.startup.name', read_only=True)
    
    class Meta:
        model = Pilot
        fields = [
            'id', 'application', 'title', 'application_title', 'challenge_title', 'startup_name',
            'start_date', 'end_date', 'status', 'total_budget', 'success_criteria', 'milestones'
        ]
        read_only_fields = ['status']

class ValidationSerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(source='expert.username', read_only=True)
    class Meta:
        model = Validation
        fields = ['id', 'submission', 'expert', 'expert_name', 'status', 'comments']
        read_only_fields = ['expert']

class MilestoneSubmissionSerializer(serializers.ModelSerializer):
    validation = ValidationSerializer(read_only=True)
    class Meta:
        model = MilestoneSubmission
        fields = ['id', 'milestone', 'actual_kpi_result', 'description', 'evidence_files', 'validation']

class PaymentSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source='milestone.pilot.application.startup.name', read_only=True)
    milestone_name = serializers.CharField(source='milestone.name', read_only=True)
    pilot_title = serializers.CharField(source='milestone.pilot.title', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'payment_id', 'milestone', 'milestone_name', 'pilot_title', 'startup_name', 'amount', 'status', 'simulated_transaction_id']
        read_only_fields = ['payment_id', 'milestone', 'amount']

class ScaleUpDecisionSerializer(serializers.ModelSerializer):
    pilot_title = serializers.CharField(source='pilot.title', read_only=True)
    startup_name = serializers.CharField(source='pilot.application.startup.name', read_only=True)
    challenge_title = serializers.CharField(source='pilot.application.challenge.title', read_only=True)

    class Meta:
        model = ScaleUpDecision
        fields = [
            'id', 'pilot', 'pilot_title', 'startup_name', 'challenge_title',
            'decision', 'reason', 'approved_budget'
        ]
