from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LogoutView,LoginView
from .models import Club, Event, Membership,Profile
from .forms import MessageForm, CustomUserCreationForm,ProfileForm,EventForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseForbidden
import json
from django.utils.safestring import mark_safe
@login_required
def my_clubs(request):
    # Example query: Fetch clubs related to the logged-in user
    user_clubs = Club.objects.filter(memberships__user=request.user, memberships__status='approved')


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
    if request.method == 'POST':
        # User is requesting to join the club
        if not membership:
            Membership.objects.create(user=request.user, club=club, status='pending')
            messages.success(request, 'Join request sent!')
        else:
            messages.info(request, 'You have already applied or are a member.')
        return redirect('club_detail', club_id=club_id)
    return render(request, 'clubs/club_detail.html', {'club': club, 'membership': membership})


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

    # Check if the current user is authorized
    is_member = Membership.objects.filter(user=request.user, club=club, status='approved').exists()

    if not is_member and request.user != club.admin:
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

    # Render the messaging template
    return render(request, 'clubs/messaging.html', {
        'club': club,
        'messages': messages_list,
        'form': form,
        'room_name': room_name,  # Pass the room name to the template
    })

@login_required
def admin_dashboard(request):
    # Verify that the user is an admin
    if not request.user.is_staff:  # Replace with a more specific condition if needed
        raise PermissionDenied("You are not authorized to view this page.")

    # Get all clubs where the user is the admin
    clubs = Club.objects.filter(admin=request.user).exclude(id__isnull=True).annotate(member_count=Count('memberships'))
    if not clubs.exists():
        print("No clubs found for this user")

    print("Clubs:", list(clubs.values()))  # Debugging output

    # Compute additional statistics
    club_names = [club.name for club in clubs]  # Club names for Chart.js
    member_counts = [club.member_count for club in clubs]  # Total members per club

    # Retrieve approved and pending memberships per club
    approved_counts = []
    pending_counts = []

    for club in clubs:
        # Count approved and pending memberships for each club
        approved = Membership.objects.filter(club=club, status='approved').count()
        pending = Membership.objects.filter(club=club, status='pending').count()

        approved_counts.append(approved)
        pending_counts.append(pending)

    # Serialize the data securely for the frontend
    context = {
        'clubs': clubs,
        'club_names': mark_safe(json.dumps(club_names)),  # Safely pass club names as JSON
        'member_counts': mark_safe(json.dumps(member_counts)),  # Safely pass member counts as JSON
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
