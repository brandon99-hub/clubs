from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views
from clubs import views as club_views
from django.contrib.auth.views import LogoutView
from .views import profile_view, CustomLogoutView


def home_redirect(request):
    """
    If the user is authenticated, redirect to the club list.
    Otherwise, redirect to the login page.
    """
    if request.user.is_authenticated:
        return redirect('club_list')
    else:
        return redirect('login')


urlpatterns = [
    path('', home_redirect, name='home'),

    # 2) Clubs & Events URLs
    path('club_list/', views.club_list, name='club_list'),  # Moved from '/' to '/club-list/'
    path('club/<int:club_id>/', views.club_detail, name='club_detail'),
    path('club/<int:club_id>/events/', views.event_list, name='event_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('club/<int:club_id>/messaging/', views.messaging, name='messaging'),
    path('club/<int:club_id>/save_message/', views.save_message_ajax, name='save_message_ajax'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:membership_id>/', views.approve_member, name='approve_member'),
    path('reject/<int:membership_id>/', views.reject_member, name='reject_member'),

    # Document URLs
    path('club/<int:club_id>/upload_document/', views.upload_document, name='upload_document'),
    path('document/<int:document_id>/download/', views.download_document, name='download_document'),

    # Google Calendar Integration URLs
    path('calendar/auth/', views.google_calendar_auth, name='google_calendar_auth'),
    path('calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('event/<int:event_id>/sync/', views.sync_event_to_calendar, name='sync_event_to_calendar'),
    path('calendar/sync-all/', views.sync_all_events, name='sync_all_events'),
    path('calendar/disconnect/', views.disconnect_google_calendar, name='disconnect_google_calendar'),

    # 3) Auth URLs
    path('signup/', club_views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my_clubs/', views.my_clubs, name='my_clubs'),
    path('club/<int:club_id>/add_event/', views.add_event, name='add_event'),
    path(
        'password_change_form/',
        auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
        name='password_change'
    ),
    path(
        'password_change_done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
        name='password_change_done'
    ),

    # Password reset URLs
    path(
        'password_reset_form/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),

    path('mark_notifications_read/', views.mark_notifications_read, name='mark_notifications_read'),

]
