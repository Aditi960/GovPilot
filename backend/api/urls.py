from django.urls import path
from .views import (
    RegisterView, LoginView, MeView,
    DepartmentListView,
    ChallengeListCreateView, ChallengeDetailView, ChallengeTransitionView,
    StartupProfileView,
    ApplicationListCreateView, ApplicationDetailView, ApplicationTransitionView,
    ExpertUsersListView, ExpertAssignmentListCreateView, EvaluationSubmitView,
    PilotListCreateView, PilotDetailView, MilestoneListCreateView,
    MilestoneSubmissionListCreateView, ValidationCreateView, PaymentListView, PaymentReleaseView
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='departments'),

    # Challenges
    path('challenges/', ChallengeListCreateView.as_view(), name='challenge-list-create'),
    path('challenges/<uuid:pk>/', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('challenges/<uuid:pk>/transition/', ChallengeTransitionView.as_view(), name='challenge-transition'),

    # Startup Profile
    path('startup/profile/', StartupProfileView.as_view(), name='startup-profile'),

    # Applications
    path('applications/', ApplicationListCreateView.as_view(), name='application-list-create'),
    path('applications/<uuid:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<uuid:pk>/transition/', ApplicationTransitionView.as_view(), name='application-transition'),

    # Experts & Evaluations
    path('experts/', ExpertUsersListView.as_view(), name='expert-users-list'),
    path('expert-assignments/', ExpertAssignmentListCreateView.as_view(), name='expert-assignment-list-create'),
    path('expert-assignments/<uuid:assignment_id>/evaluate/', EvaluationSubmitView.as_view(), name='evaluation-submit'),

    # Pilots & Milestones
    path('pilots/', PilotListCreateView.as_view(), name='pilot-list-create'),
    path('pilots/<uuid:pk>/', PilotDetailView.as_view(), name='pilot-detail'),
    path('milestones/', MilestoneListCreateView.as_view(), name='milestone-list-create'),

    # Submissions & Validations
    path('submissions/', MilestoneSubmissionListCreateView.as_view(), name='submission-list-create'),
    path('submissions/<uuid:submission_id>/validate/', ValidationCreateView.as_view(), name='validation-create'),

    # Payments
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/release/', PaymentReleaseView.as_view(), name='payment-release'),
]
