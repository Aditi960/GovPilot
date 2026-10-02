import uuid
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from .models import (
    User, Challenge, ChallengeStatus, GovernmentDepartment,
    Application, ApplicationStatus, AuditLog, ExpertAssignment, Evaluation, Role,
    Pilot, PilotMilestone, MilestoneSubmission, Validation, Payment, MilestoneStatus, ValidationStatus, PaymentStatus
)
from .serializers import (
    UserSerializer, ChallengeSerializer, GovernmentDepartmentSerializer,
    StartupSerializer, ApplicationSerializer, ExpertAssignmentSerializer,
    EvaluationSerializer, PilotSerializer, PilotMilestoneSerializer,
    MilestoneSubmissionSerializer, ValidationSerializer, PaymentSerializer
)
from .permissions import IsGovernmentOfficer, IsGovernmentOrReadOnly


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def create_audit_log(user, action, entity_type, entity_id, previous_state="", new_state=""):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
    )


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role', 'STARTUP')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ──────────────────────────────────────────────
# Departments
# ──────────────────────────────────────────────
class DepartmentListView(generics.ListAPIView):
    queryset = GovernmentDepartment.objects.all()
    serializer_class = GovernmentDepartmentSerializer
    permission_classes = [IsAuthenticated]


# ──────────────────────────────────────────────
# Challenges
# ──────────────────────────────────────────────
CHALLENGE_VALID_TRANSITIONS = {
    ChallengeStatus.DRAFT: [ChallengeStatus.PUBLISHED],
    ChallengeStatus.PUBLISHED: [ChallengeStatus.APPLICATIONS_OPEN],
    ChallengeStatus.APPLICATIONS_OPEN: [ChallengeStatus.APPLICATIONS_CLOSED],
    ChallengeStatus.APPLICATIONS_CLOSED: [ChallengeStatus.EVALUATION],
    ChallengeStatus.EVALUATION: [ChallengeStatus.SELECTION],
    ChallengeStatus.SELECTION: [ChallengeStatus.COMPLETED],
}


class ChallengeListCreateView(generics.ListCreateAPIView):
    serializer_class = ChallengeSerializer
    permission_classes = [IsGovernmentOrReadOnly]

    def get_queryset(self):
        qs = Challenge.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        department = self.request.query_params.get('department')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(title__icontains=search)
        if department:
            qs = qs.filter(department__name__icontains=department)

        # Public can only see published+
        if not self.request.user.is_authenticated or self.request.user.role not in ['GOVERNMENT', 'ADMIN']:
            qs = qs.exclude(status=ChallengeStatus.DRAFT)

        return qs

    def perform_create(self, serializer):
        challenge = serializer.save()
        create_audit_log(
            self.request.user, 'CHALLENGE_CREATED', 'Challenge',
            challenge.id, '', ChallengeStatus.DRAFT
        )


class ChallengeDetailView(generics.RetrieveUpdateAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsGovernmentOrReadOnly]

    def perform_update(self, serializer):
        challenge = serializer.save()
        create_audit_log(
            self.request.user, 'CHALLENGE_UPDATED', 'Challenge',
            challenge.id, '', challenge.status
        )


class ChallengeTransitionView(APIView):
    """POST /api/challenges/:id/transition/ with body {"status": "PUBLISHED"}"""
    permission_classes = [IsGovernmentOfficer]

    def post(self, request, pk):
        challenge = get_object_or_404(Challenge, pk=pk)
        new_status = request.data.get('status')
        allowed = CHALLENGE_VALID_TRANSITIONS.get(challenge.status, [])

        if new_status not in allowed:
            return Response(
                {'error': f'Cannot transition from {challenge.status} to {new_status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prev = challenge.status
        challenge.status = new_status
        challenge.save()

        create_audit_log(
            request.user, 'CHALLENGE_STATUS_CHANGED', 'Challenge',
            challenge.id, prev, new_status
        )
        return Response(ChallengeSerializer(challenge).data)

# ──────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────
class StartupProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'startup_profile'):
            return Response({'error': 'No startup profile found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StartupSerializer(request.user.startup_profile)
        return Response(serializer.data)

    def post(self, request):
        if hasattr(request.user, 'startup_profile'):
            serializer = StartupSerializer(request.user.startup_profile, data=request.data, partial=True)
        else:
            serializer = StartupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ──────────────────────────────────────────────
# Applications
# ──────────────────────────────────────────────
class ApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Application.objects.all().order_by('-created_at')
        user = self.request.user
        if user.role == 'STARTUP' and hasattr(user, 'startup_profile'):
            qs = qs.filter(startup=user.startup_profile)
        elif user.role == 'GOVERNMENT':
            qs = qs.filter(challenge__department__officer=user)
        # EXPERT/ADMIN can see what they are assigned to / all
        challenge_id = self.request.query_params.get('challenge')
        if challenge_id:
            qs = qs.filter(challenge_id=challenge_id)
        return qs

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'startup_profile'):
            raise serializers.ValidationError("Only startups can apply.")
        app = serializer.save(startup=self.request.user.startup_profile, status=ApplicationStatus.SUBMITTED)
        create_audit_log(self.request.user, 'APPLICATION_SUBMITTED', 'Application', app.id, '', app.status)

class ApplicationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        app = serializer.save()
        create_audit_log(self.request.user, 'APPLICATION_UPDATED', 'Application', app.id, '', app.status)

class ApplicationTransitionView(APIView):
    permission_classes = [IsGovernmentOfficer]
    
    def post(self, request, pk):
        app = get_object_or_404(Application, pk=pk)
        new_status = request.data.get('status')
        eligibility_notes = request.data.get('eligibility_notes', '')

        # Simplified state machine for demo
        valid_statuses = [c[0] for c in ApplicationStatus.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        prev = app.status
        app.status = new_status
        if eligibility_notes:
            app.eligibility_notes = eligibility_notes
        app.save()

        create_audit_log(request.user, 'APPLICATION_STATUS_CHANGED', 'Application', app.id, prev, new_status)
        return Response(ApplicationSerializer(app).data)

# ──────────────────────────────────────────────
# Experts & Evaluation
# ──────────────────────────────────────────────
class ExpertUsersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsGovernmentOfficer]

    def get_queryset(self):
        return User.objects.filter(role=Role.EXPERT)

class ExpertAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpertAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ExpertAssignment.objects.all()
        user = self.request.user
        if user.role == 'EXPERT':
            qs = qs.filter(expert=user)
        elif user.role == 'GOVERNMENT':
            qs = qs.filter(application__challenge__department__officer=user)
        
        app_id = self.request.query_params.get('application')
        if app_id:
            qs = qs.filter(application_id=app_id)
        return qs

    def perform_create(self, serializer):
        assignment = serializer.save()
        create_audit_log(
            self.request.user, 'EXPERT_ASSIGNED', 'ExpertAssignment',
            assignment.id, '', str(assignment.expert.username)
        )

class EvaluationSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        assignment = get_object_or_404(ExpertAssignment, pk=assignment_id)
        
        if request.user.role != 'EXPERT' or assignment.expert != request.user:
            return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
            
        scores = request.data.get('criteria_scores', {})
        comments = request.data.get('comments', '')
        
        challenge = assignment.application.challenge
        criteria = challenge.evaluation_criteria.all()
        
        final_score = 0
        for crit in criteria:
            score = float(scores.get(str(crit.id), 0))
            # Assuming score is out of 100 for that specific criterion
            # Contribution = (score * weight) / 100
            final_score += (score * crit.weight_percentage) / 100.0

        eval_obj, created = Evaluation.objects.update_or_create(
            assignment=assignment,
            defaults={
                'criteria_scores': scores,
                'comments': comments,
                'final_score': final_score
            }
        )
        
        create_audit_log(
            request.user, 'EVALUATION_SUBMITTED', 'Evaluation',
            eval_obj.id, '', str(final_score)
        )
        
        return Response(EvaluationSerializer(eval_obj).data)

# ──────────────────────────────────────────────
# Pilots & Milestones
# ──────────────────────────────────────────────
class PilotListCreateView(generics.ListCreateAPIView):
    serializer_class = PilotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Pilot.objects.all()
        user = self.request.user
        if user.role == 'STARTUP' and hasattr(user, 'startup_profile'):
            qs = qs.filter(application__startup=user.startup_profile)
        elif user.role == 'GOVERNMENT':
            qs = qs.filter(application__challenge__department__officer=user)
        
        app_id = self.request.query_params.get('application')
        if app_id:
            qs = qs.filter(application_id=app_id)
        return qs

    def perform_create(self, serializer):
        # The pilot should be created only by Government
        if self.request.user.role != 'GOVERNMENT':
            raise serializers.ValidationError("Only Government Officers can create pilots.")
            
        pilot = serializer.save(status='ACTIVE')
        app = pilot.application
        if app.status != ApplicationStatus.SELECTED:
            app.status = ApplicationStatus.SELECTED
            app.save()

        create_audit_log(
            self.request.user, 'PILOT_INITIATED', 'Pilot',
            pilot.id, '', 'ACTIVE'
        )

class PilotDetailView(generics.RetrieveUpdateAPIView):
    queryset = Pilot.objects.all()
    serializer_class = PilotSerializer
    permission_classes = [IsAuthenticated]

class MilestoneListCreateView(generics.ListCreateAPIView):
    serializer_class = PilotMilestoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pilot_id = self.request.query_params.get('pilot')
        qs = PilotMilestone.objects.all().order_by('due_date')
        if pilot_id:
            qs = qs.filter(pilot_id=pilot_id)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role != 'GOVERNMENT':
            raise serializers.ValidationError("Only Government Officers can create milestones.")
        serializer.save(status='PENDING')

# ──────────────────────────────────────────────
# Milestone Submission & Validation (Phase 7)
# ──────────────────────────────────────────────
class MilestoneSubmissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MilestoneSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = MilestoneSubmission.objects.all()
        milestone_id = self.request.query_params.get('milestone')
        if milestone_id:
            qs = qs.filter(milestone_id=milestone_id)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role != 'STARTUP':
            raise serializers.ValidationError("Only Startups can submit milestone evidence.")
        
        milestone = serializer.validated_data['milestone']
        if milestone.status not in [MilestoneStatus.NOT_STARTED, MilestoneStatus.PENDING, MilestoneStatus.REJECTED]:
            raise serializers.ValidationError("Milestone is not in a state to accept submissions.")

        submission = serializer.save()
        milestone.status = MilestoneStatus.SUBMITTED
        milestone.save()

        create_audit_log(
            self.request.user, 'MILESTONE_SUBMITTED', 'MilestoneSubmission',
            submission.id, '', 'SUBMITTED'
        )

class ValidationCreateView(generics.CreateAPIView):
    serializer_class = ValidationSerializer
    permission_classes = [IsAuthenticated, IsGovernmentOfficer]

    def perform_create(self, serializer):
        submission_id = self.kwargs['submission_id']
        submission = get_object_or_404(MilestoneSubmission, id=submission_id)
        
        validation = serializer.save(submission=submission, expert=self.request.user)
        milestone = submission.milestone

        if validation.status == ValidationStatus.VERIFIED:
            milestone.status = MilestoneStatus.VERIFIED
            milestone.save()
            
            # Auto-generate a locked Payment record
            payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
            Payment.objects.create(
                payment_id=payment_id,
                milestone=milestone,
                amount=milestone.payment_amount,
                status=PaymentStatus.LOCKED
            )
        elif validation.status == ValidationStatus.REJECTED or validation.status == ValidationStatus.REQUEST_CORRECTION:
            milestone.status = MilestoneStatus.REJECTED
            milestone.save()

        create_audit_log(
            self.request.user, f'MILESTONE_{validation.status}', 'Validation',
            validation.id, '', validation.status
        )

# ──────────────────────────────────────────────
# Simulated Payments (Phase 7)
# ──────────────────────────────────────────────
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Payment.objects.all()
        user = self.request.user
        if user.role == 'STARTUP' and hasattr(user, 'startup_profile'):
            qs = qs.filter(milestone__pilot__application__startup=user.startup_profile)
        elif user.role == 'GOVERNMENT':
            qs = qs.filter(milestone__pilot__application__challenge__department__officer=user)
        return qs

class PaymentReleaseView(APIView):
    permission_classes = [IsAuthenticated, IsGovernmentOfficer]

    def post(self, request, pk):
        payment = get_object_or_404(Payment, id=pk)
        
        if payment.status in [PaymentStatus.RELEASED]:
            return Response({"error": "Payment is already released."}, status=status.HTTP_400_BAD_REQUEST)

        # Simulate transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        payment.status = PaymentStatus.RELEASED
        payment.simulated_transaction_id = transaction_id
        payment.save()
        
        # Update milestone
        payment.milestone.status = MilestoneStatus.PAID
        payment.milestone.save()

        create_audit_log(
            request.user, 'PAYMENT_RELEASED', 'Payment',
            payment.id, 'LOCKED', 'RELEASED'
        )

        return Response(PaymentSerializer(payment).data)
