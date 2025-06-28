from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LogoutView,LoginView
from .models import Club, Event, Membership,Profile, Notification, Document, GoogleCalendarToken, Message
from .forms import MessageForm, CustomUserCreationForm,ProfileForm,EventForm, DocumentForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.db.models import Q
from .services.google_calendar import GoogleCalendarService
from django.views.decorators.csrf import csrf_exempt

@login_required
def my_clubs(request):
    # Get clubs where user is a member (approved membership)
    member_clubs = Club.objects.filter(memberships__user=request.user, memberships__status='approved')
    
    # Get clubs where user is the admin
    admin_clubs = Club.objects.filter(admin=request.user)
    
    # Combine both querysets and remove duplicates
    user_clubs = (member_clubs | admin_clubs).distinct().order_by('name')

    return render(request, 'clubs/my_clubs.html', {'user_clubs': user_clubs})

@login_required
def user_settings(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        subscribed_to_emails = request.POST.get('subscribed_to_emails') == 'on'
        profile.subscribed_to_emails = subscribed_to_emails
        profile.save()
        return redirect('settings')

    return render(request, 'clubs/settings.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile,user=request.user)
    return render(request, 'clubs/edit_profile.html', {'form': form})


class CustomLoginView(LoginView):
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else '/club_list/'

    def form_valid(self, form):
        # Check if the logged-in user's profile exists
        user = form.get_user()
        if not hasattr(user, 'profile'):
            # Optionally, create a profile if missing (or handle gracefully)
            from clubs.models import Profile
            Profile.objects.create(user=user)
        return super().form_valid(form)


@login_required
def post_login_redirect(request):
    # Redirect to a different page if the profile is missing
    if not hasattr(request.user, 'profile'):
        return redirect('create_profile')  # Route to create a profile manually (optional)
    return redirect('dashboard')  # Redirect to your dashboard or any default page


class CustomLogoutView(LogoutView):
    """
    Allows both GET and POST for logout.
    If you're getting a 405 error on GET, this resolves it.
    """
    http_method_names = ['get', 'post']
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        return redirect('/login/')


def signup(request):
    """
    Renders a signup form using CustomUserCreationForm.
    On POST, if valid, creates a user and redirects to 'login'.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def club_list(request):
    if not request.user.is_authenticated:
        # Add a warning message for unauthenticated users
        messages.warning(request, "You need to log in to view the list of clubs.")
        return redirect('login')  # Redirect to the login page

    query = request.GET.get('q', '')  # Get 'q' parameter from request
    if query:  # If the user has searched for something
        clubs = Club.objects.filter(name__icontains=query) | Club.objects.filter(description__icontains=query)
    else:  # Otherwise, return all clubs
        clubs = Club.objects.all().order_by('name')  # Default ordering

    # Use paginator for paginating clubs
    paginator = Paginator(clubs, 10)  # 10 clubs per page
    page_number = request.GET.get('page')  # Get the page number from request
    page_obj = paginator.get_page(page_number)

    return render(request, 'clubs/club_list.html',
                  {'page_obj': page_obj, 'clubs': page_obj.object_list, 'query': query})



@login_required
def club_detail(request, club_id):
    """
    Shows details about a specific club.
    Allows a user to request membership if they haven't already.
    """
    club = get_object_or_404(Club, id=club_id)
    membership = Membership.objects.filter(user=request.user, club=club).first()
    
    # Get all members including the admin
    all_members = club.get_all_members()
    
    if request.method == 'POST':
        # User is requesting to join the club
        if not membership:
            Membership.objects.create(user=request.user, club=club, status='pending')
            messages.success(request, 'Join request sent!')
        else:
            messages.info(request, 'You have already applied or are a member.')
        return redirect('club_detail', club_id=club_id)
    
    return render(request, 'clubs/club_detail.html', {
        'club': club, 
        'membership': membership,
        'approved_memberships': all_members
    })


@login_required
def event_list(request, club_id):
    """
    Lists events for a given club.
    """
    club = get_object_or_404(Club, id=club_id)
    events = club.events.all()
    return render(request, 'clubs/event_list.html', {'club': club, 'events': events})


@login_required
def event_detail(request, event_id):
    """
    Displays details of a specific event.
    """
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'clubs/event_detail.html', {'event': event})


@login_required
def messaging(request, club_id):
    # Fetch the club or raise a 404
    club = get_object_or_404(Club, id=club_id)

    # Check if the current user is authorized (member or admin)
    if not club.is_user_member(request.user):
        messages.warning(request, "You must be an approved member to access the messaging feature.")
        return redirect('club_detail', club_id=club_id)

    # Ensure the admin has a profile (if current user is admin)
    if request.user == club.admin:
        Profile.objects.get_or_create(user=request.user)

    # Room name for WebSocket communication
    room_name = f"club_{club_id}"

    # Initialize MessageForm for adding new messages
    form = MessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        message = form.save(commit=False)
        message.club = club
        message.sender = request.user
        message.save()
        return redirect('messaging', club_id=club.id)

    # Fetch the messages for the club
    messages_list = club.messages.order_by('timestamp')
    
    # Fetch documents for the club
    documents = club.documents.all()

    # Render the messaging template
    return render(request, 'clubs/messaging.html', {
        'club': club,
        'chat_messages': messages_list,
        'documents': documents,
        'form': form,
        'room_name': room_name,  # Pass the room name to the template
    })

@login_required
def admin_dashboard(request):
    # Verify that the user is an admin of at least one club
    user_clubs = Club.objects.filter(admin=request.user)
    if not user_clubs.exists():
        messages.error(request, "You are not an admin of any clubs.")
        return redirect('club_list')

    # Get all clubs where the user is the admin
    clubs = user_clubs.exclude(id__isnull=True)
    if not clubs.exists():
        print("No clubs found for this user")

    print("Clubs:", list(clubs.values()))  # Debugging output

    # Pagination for clubs - 4 clubs per page (2x2 grid)
    paginator = Paginator(clubs, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get pending and approved memberships for each club on the current page
    pending_memberships = {}
    approved_members = {}
    
    for club in page_obj.object_list:
        pending_memberships[club.id] = Membership.objects.filter(club=club, status='pending').select_related('user')
        # Get all members including admin
        approved_members[club.id] = club.get_all_members()

    # Compute additional statistics for charts (all clubs, not just current page)
    all_clubs = clubs  # Use all clubs for chart data
    club_names = [club.name for club in all_clubs]  # Club names for Chart.js
    approved_counts = []
    pending_counts = []
    
    for club in all_clubs:
        # Count all members including admin
        approved_count = len(club.get_all_members())
        pending_count = Membership.objects.filter(club=club, status='pending').count()
        approved_counts.append(approved_count)
        pending_counts.append(pending_count)

    # Serialize the data securely for the frontend
    context = {
        'clubs': page_obj.object_list,
        'page_obj': page_obj,
        'pending_memberships': pending_memberships,
        'approved_members': approved_members,
        'club_names': mark_safe(json.dumps(club_names)),  # Safely pass club names as JSON
        'approved_counts': mark_safe(json.dumps(approved_counts)),  # Approved members data
        'pending_counts': mark_safe(json.dumps(pending_counts)),  # Pending members data
    }

    return render(request, 'clubs/admin_dashboard.html', context)


@login_required
def approve_member(request, membership_id):
    """
    Approves a user's membership request if the current user is the club admin.
    """
    membership = Membership.objects.get(id=membership_id)
    if request.user != membership.club.admin:
        raise PermissionDenied("You are not allowed to approve members.")

    membership = get_object_or_404(Membership, id=membership_id)
    if request.user != membership.club.admin:
        messages.error(request, "Not authorized.")
        return redirect('admin_dashboard')
    membership.status = 'approved'
    membership.save()
    messages.success(request, f"{membership.user.username} approved for {membership.club.name}.")
    return redirect('admin_dashboard')

@login_required
def reject_member(request, membership_id):
    """
    Rejects a user's membership request if the current user is the club admin.
    """
    membership = get_object_or_404(Membership, id=membership_id)
    if request.user != membership.club.admin:
        messages.error(request, "Not authorized.")
        return redirect('admin_dashboard')
    membership.status = 'declined'
    membership.save()
    messages.success(request, f"{membership.user.username} rejected for {membership.club.name}.")
    return redirect('admin_dashboard')

@login_required
def profile_view(request):
    if hasattr(request.user, 'profile'):
        bio = request.user.profile.bio
    else:
        bio = None  # Fallback if the profile doesn't exist

    context = {
        'user': request.user,
        'bio': bio,
    }

    return render(request, 'clubs/profile.html')

@login_required
def add_event(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    # Only allow the admin of the club to create events
    if request.user != club.admin:
        return HttpResponseForbidden("Only the admin can add events.")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.club = club
            event.save()
            return redirect('club_detail', club_id=club_id)
    else:
        form = EventForm()

    return render(request, 'clubs/add_event.html', {'club': club, 'form': form})

@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return HttpResponse(status=204)

@login_required
def upload_document(request, club_id):
    """Upload a document to a club."""
    club = get_object_or_404(Club, id=club_id)
    
    # Check if the current user is authorized (member or admin)
    if not club.is_user_member(request.user):
        messages.error(request, "You must be an approved member to upload documents.")
        return redirect('club_detail', club_id=club_id)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.club = club
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f"Document '{document.title}' uploaded successfully!")
            return redirect('messaging', club_id=club_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentForm()
    
    return render(request, 'clubs/upload_document.html', {
        'club': club,
        'form': form
    })

@login_required
def download_document(request, document_id):
    """Download a document."""
    document = get_object_or_404(Document, id=document_id)
    
    # Check if user has access to the document (member or admin)
    if not document.club.is_user_member(request.user):
        messages.error(request, "You don't have permission to access this document.")
        return redirect('club_detail', club_id=document.club.id)
    
    # Check if document is public or user is admin
    if not document.is_public and request.user != document.club.admin:
        messages.error(request, "This document is not publicly accessible.")
        return redirect('club_detail', club_id=document.club.id)
    
    # Serve the file
    response = HttpResponse(document.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
    return response

# Google Calendar Integration Views
@login_required
def google_calendar_auth(request):
    """Initiate Google Calendar OAuth2 flow"""
    calendar_service = GoogleCalendarService(request.user)
    auth_url = calendar_service.create_auth_url()
    return redirect(auth_url)

@login_required
def google_calendar_callback(request):
    """Handle Google Calendar OAuth2 callback"""
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Authorization failed. Please try again.')
        return redirect('settings')
    
    try:
        calendar_service = GoogleCalendarService(request.user)
        calendar_service.exchange_code_for_token(code)
        messages.success(request, 'Google Calendar connected successfully!')
    except Exception as e:
        messages.error(request, f'Failed to connect Google Calendar: {str(e)}')
    
    return redirect('settings')

@login_required
def sync_event_to_calendar(request, event_id):
    """Sync a specific event to Google Calendar"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user is admin of the event's club
    if event.club.admin != request.user:
        messages.error(request, 'You can only sync events from your own clubs.')
        return redirect('event_detail', event_id=event_id)
    
    try:
        calendar_service = GoogleCalendarService(request.user)
        result, error = calendar_service.create_event(event)
        
        if result:
            messages.success(request, f'Event "{event.title}" synced to Google Calendar!')
        else:
            messages.error(request, f'Failed to sync event: {error}')
            
    except Exception as e:
        messages.error(request, f'Failed to sync event: {str(e)}')
    
    return redirect('event_detail', event_id=event_id)

@login_required
def sync_all_events(request):
    """Sync all user's events to Google Calendar"""
    try:
        calendar_service = GoogleCalendarService(request.user)
        results = calendar_service.sync_all_events()
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        if success_count > 0:
            messages.success(request, f'Successfully synced {success_count} out of {total_count} events to Google Calendar.')
        else:
            messages.warning(request, 'No events were synced. Please check your Google Calendar connection.')
            
    except Exception as e:
        messages.error(request, f'Failed to sync events: {str(e)}')
    
    return redirect('admin_dashboard')

@login_required
def disconnect_google_calendar(request):
    """Disconnect Google Calendar integration"""
    try:
        GoogleCalendarToken.objects.filter(user=request.user).delete()
        messages.success(request, 'Google Calendar disconnected successfully.')
    except Exception as e:
        messages.error(request, f'Failed to disconnect: {str(e)}')
    
    return redirect('settings')

@login_required
def profile(request):
    return render(request, 'clubs/profile.html')

@login_required
def settings(request):
    """User settings page"""
    if request.method == 'POST':
        # Handle email subscription toggle
        subscribed_to_emails = request.POST.get('subscribed_to_emails') == 'on'
        profile = request.user.profile
        profile.subscribed_to_emails = subscribed_to_emails
        profile.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')
    
    return render(request, 'clubs/settings.html')

@login_required
@require_POST
def save_message_ajax(request, club_id):
    """AJAX endpoint to save messages to database without page reload."""
    try:
        club = get_object_or_404(Club, id=club_id)
        
        # Check if the current user is authorized (member or admin)
        if not club.is_user_member(request.user):
            return JsonResponse({'error': 'You must be an approved member to send messages.'}, status=403)
        
        # Parse JSON data
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        # Validate message content
        if not content:
            return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)
        
        if len(content) > 500:
            return JsonResponse({'error': 'Message too long. Maximum 500 characters.'}, status=400)
        
        # Create and save the message
        message = Message.objects.create(
            club=club,
            sender=request.user,
            content=content
        )
        
        # Return success response with message data
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender_username': message.sender.username
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while saving the message.'}, status=500)
