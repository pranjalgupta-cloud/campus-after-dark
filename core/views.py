from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
import datetime


def home(request):
    from facilities.models import Facility
    from accounts.models import InstitutionProfile
    featured = Facility.objects.filter(
        status=Facility.STATUS_PUBLISHED,
        institution__verification_status=InstitutionProfile.STATUS_APPROVED,
        is_featured=True
    ).select_related('institution').prefetch_related('images')[:6]

    if featured.count() < 3:
        featured = Facility.objects.filter(
            status=Facility.STATUS_PUBLISHED,
            institution__verification_status=InstitutionProfile.STATUS_APPROVED
        ).select_related('institution').prefetch_related('images')[:6]

    from facilities.models import Facility as F
    categories = F.CATEGORY_CHOICES

    # Platform stats (from real data + demo labels)
    from accounts.models import User
    from bookings.models import Booking
    stats = {
        'institutions': InstitutionProfile.objects.filter(verification_status='approved').count(),
        'facilities': Facility.objects.filter(status='published').count(),
        'bookings': Booking.objects.filter(status__in=['confirmed', 'completed']).count(),
        'cities': Facility.objects.filter(status='published').values('city').distinct().count(),
    }
    return render(request, 'public/home.html', {
        'featured_facilities': featured,
        'categories': categories,
        'stats': stats,
    })


def how_it_works(request):
    return render(request, 'public/how_it_works.html')


def for_institutions(request):
    return render(request, 'public/for_institutions.html')


def for_organizations(request):
    return render(request, 'public/for_organizations.html')


def about(request):
    return render(request, 'public/about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message. We will get back to you within 24 hours.')
        return redirect('contact')
    return render(request, 'public/contact.html')





def privacy_policy(request):
    return render(request, 'public/privacy.html')


def terms(request):
    return render(request, 'public/terms.html')


def handler404(request, exception):
    return render(request, 'public/404.html', status=404)


@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on role."""
    user = request.user
    if user.is_platform_admin:
        return redirect('admin_dashboard')
    elif user.is_institution:
        return redirect('institution_dashboard')
    elif user.is_org:
        return redirect('org_dashboard')
    return redirect('home')


# â”€â”€â”€ Institution Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required
def institution_dashboard(request):
    if not request.user.is_institution:
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except Exception:
        return redirect('institution_setup')

    from bookings.models import Booking, Notification
    from facilities.models import Facility

    now = timezone.now()
    today = now.date()
    first_of_month = today.replace(day=1)

    facilities = Facility.objects.filter(institution=profile)
    all_bookings = Booking.objects.filter(facility__institution=profile)

    total_facilities = facilities.count()
    pending_requests = all_bookings.filter(status=Booking.STATUS_PENDING).count()
    upcoming_bookings = all_bookings.filter(
        status=Booking.STATUS_CONFIRMED, booked_date__gte=today
    ).count()

    monthly_revenue = all_bookings.filter(
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED],
        booked_date__gte=first_of_month
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0')

    monthly_commission = all_bookings.filter(
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED],
        booked_date__gte=first_of_month
    ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    monthly_payout = monthly_revenue - monthly_commission

    recent_bookings = all_bookings.select_related(
        'facility', 'organization'
    ).order_by('-created_at')[:10]

    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:5]

    # Monthly revenue chart data (last 6 months)
    chart_labels = []
    chart_revenue = []
    chart_commission = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - datetime.timedelta(days=i*30)).replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            month_end = next_month - datetime.timedelta(days=1)
        month_data = all_bookings.filter(
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED],
            booked_date__gte=month_start,
            booked_date__lte=month_end
        ).aggregate(rev=Sum('subtotal'), comm=Sum('commission_amount'))
        chart_labels.append(month_start.strftime('%b %Y'))
        chart_revenue.append(float(month_data['rev'] or 0))
        chart_commission.append(float(month_data['comm'] or 0))

    return render(request, 'dashboards/institution.html', {
        'profile': profile,
        'total_facilities': total_facilities,
        'pending_requests': pending_requests,
        'upcoming_bookings': upcoming_bookings,
        'monthly_revenue': monthly_revenue,
        'monthly_commission': monthly_commission,
        'monthly_payout': monthly_payout,
        'recent_bookings': recent_bookings,
        'notifications': notifications,
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
        'chart_commission': chart_commission,
        'facilities': facilities[:5],
    })


# â”€â”€â”€ Organization Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required
def org_dashboard(request):
    if not request.user.is_org:
        return redirect('dashboard')
    try:
        org = request.user.org_profile
    except Exception:
        return redirect('profile')

    from bookings.models import Booking, Notification
    today = timezone.now().date()

    bookings = Booking.objects.filter(organization=org)
    total_requests = bookings.count()
    pending_approvals = bookings.filter(status=Booking.STATUS_PENDING).count()
    awaiting_payment = bookings.filter(status=Booking.STATUS_APPROVED).count()
    upcoming = bookings.filter(status=Booking.STATUS_CONFIRMED, booked_date__gte=today).count()
    completed = bookings.filter(status=Booking.STATUS_COMPLETED).count()

    recent_bookings = bookings.select_related(
        'facility', 'facility__institution'
    ).order_by('-created_at')[:8]

    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:5]

    return render(request, 'dashboards/organization.html', {
        'org': org,
        'total_requests': total_requests,
        'pending_approvals': pending_approvals,
        'awaiting_payment': awaiting_payment,
        'upcoming': upcoming,
        'completed': completed,
        'recent_bookings': recent_bookings,
        'notifications': notifications,
    })


# â”€â”€â”€ Admin Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required
def admin_dashboard(request):
    if not request.user.is_platform_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from accounts.models import User, InstitutionProfile, OrganizationProfile
    from facilities.models import Facility
    from bookings.models import Booking, Payment, PlatformSetting, AuditLog
    today = timezone.now().date()
    first_of_month = today.replace(day=1)

    total_institutions = InstitutionProfile.objects.count()
    pending_verifications = InstitutionProfile.objects.filter(verification_status='pending').count()
    total_orgs = OrganizationProfile.objects.count()
    active_facilities = Facility.objects.filter(status='published').count()
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status__in=['confirmed', 'completed'])
    gross_revenue = confirmed_bookings.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
    commission_revenue = confirmed_bookings.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')

    monthly_revenue = Booking.objects.filter(
        status__in=['confirmed', 'completed'],
        booked_date__gte=first_of_month
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0')

    pending_institutions = InstitutionProfile.objects.filter(
        verification_status='pending'
    ).select_related('user').order_by('-created_at')[:10]

    recent_bookings = Booking.objects.select_related(
        'facility', 'organization'
    ).order_by('-created_at')[:10]

    recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:15]

    # Chart data
    chart_labels = []
    chart_bookings = []
    chart_revenue = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - datetime.timedelta(days=i*30)).replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            month_end = next_month - datetime.timedelta(days=1)
        mdata = Booking.objects.filter(
            status__in=['confirmed', 'completed'],
            booked_date__gte=month_start,
            booked_date__lte=month_end
        ).aggregate(cnt=Count('id'), rev=Sum('subtotal'))
        chart_labels.append(month_start.strftime('%b %Y'))
        chart_bookings.append(mdata['cnt'] or 0)
        chart_revenue.append(float(mdata['rev'] or 0))

    commission_rate = PlatformSetting.get_commission_rate()

    return render(request, 'dashboards/admin.html', {
        'total_institutions': total_institutions,
        'pending_verifications': pending_verifications,
        'total_orgs': total_orgs,
        'active_facilities': active_facilities,
        'total_bookings': total_bookings,
        'gross_revenue': gross_revenue,
        'commission_revenue': commission_revenue,
        'monthly_revenue': monthly_revenue,
        'pending_institutions': pending_institutions,
        'recent_bookings': recent_bookings,
        'recent_logs': recent_logs,
        'chart_labels': chart_labels,
        'chart_bookings': chart_bookings,
        'chart_revenue': chart_revenue,
        'commission_rate': commission_rate,
    })


@login_required
def admin_institutions(request):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    from accounts.models import InstitutionProfile
    status_filter = request.GET.get('status', '')
    institutions = InstitutionProfile.objects.select_related('user').order_by('-created_at')
    if status_filter:
        institutions = institutions.filter(verification_status=status_filter)
    from django.core.paginator import Paginator
    page_obj = Paginator(institutions, 20).get_page(request.GET.get('page'))
    return render(request, 'dashboards/admin_institutions.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
    })


@login_required
def admin_approve_institution(request, pk):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    if request.method == 'POST':
        from accounts.models import InstitutionProfile
        from bookings.models import AuditLog, Notification
        inst = get_object_or_404(InstitutionProfile, pk=pk)
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        if action == 'approve':
            inst.verification_status = InstitutionProfile.STATUS_APPROVED
            inst.verified_at = timezone.now()
            inst.rejection_reason = ''
            inst.save()
            Notification.objects.create(
                user=inst.user,
                notification_type='institution_approved',
                title='Institution Approved!',
                message=f'Congratulations! {inst.name} has been verified. You can now create and publish facilities.'
            )
            AuditLog.objects.create(
                user=request.user, action='Approved institution',
                model_name='InstitutionProfile', object_id=str(pk),
                details={'institution': inst.name}
            )
            messages.success(request, f'{inst.name} approved.')
        elif action == 'reject':
            inst.verification_status = InstitutionProfile.STATUS_REJECTED
            inst.rejection_reason = reason
            inst.save()
            Notification.objects.create(
                user=inst.user,
                notification_type='institution_rejected',
                title='Institution Verification Update',
                message=f'Your institution {inst.name} verification was not approved. Reason: {reason}'
            )
            AuditLog.objects.create(
                user=request.user, action='Rejected institution',
                model_name='InstitutionProfile', object_id=str(pk),
                details={'institution': inst.name, 'reason': reason}
            )
            messages.warning(request, f'{inst.name} rejected.')
        elif action == 'suspend':
            inst.verification_status = InstitutionProfile.STATUS_SUSPENDED
            inst.save()
            AuditLog.objects.create(
                user=request.user, action='Suspended institution',
                model_name='InstitutionProfile', object_id=str(pk),
                details={'institution': inst.name}
            )
            messages.warning(request, f'{inst.name} suspended.')
    return redirect('admin_institutions')


@login_required
def admin_settings(request):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    from bookings.models import PlatformSetting, AuditLog
    if request.method == 'POST':
        commission_rate = request.POST.get('commission_rate', '').strip()
        try:
            rate = Decimal(commission_rate)
            if rate < 0 or rate > 50:
                messages.error(request, 'Commission rate must be between 0% and 50%.')
            else:
                setting, _ = PlatformSetting.objects.get_or_create(
                    key='commission_rate',
                    defaults={'value': '10', 'description': 'Platform commission percentage'}
                )
                old_val = setting.value
                setting.value = str(rate)
                setting.updated_by = request.user
                setting.save()
                AuditLog.objects.create(
                    user=request.user,
                    action=f'Changed commission rate from {old_val}% to {rate}%',
                    model_name='PlatformSetting',
                    object_id='commission_rate',
                )
                messages.success(request, f'Commission rate updated to {rate}%.')
        except Exception:
            messages.error(request, 'Invalid commission rate value.')
        return redirect('admin_settings')

    from bookings.models import PlatformSetting
    commission_rate = PlatformSetting.get_commission_rate()
    return render(request, 'dashboards/admin_settings.html', {
        'commission_rate': commission_rate,
    })


@login_required
def admin_users(request):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    from accounts.models import User
    users = User.objects.all().order_by('-created_at')
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    if q:
        users = users.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if role:
        users = users.filter(role=role)
    from django.core.paginator import Paginator
    page_obj = Paginator(users, 20).get_page(request.GET.get('page'))
    return render(request, 'dashboards/admin_users.html', {
        'page_obj': page_obj, 'q': q, 'role': role,
    })


@login_required
def admin_toggle_user(request, pk):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    if request.method == 'POST':
        from accounts.models import User
        from bookings.models import AuditLog
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'Cannot modify your own account status.')
            return redirect('admin_users')
        action = request.POST.get('action')
        if action == 'suspend':
            user.account_status = User.STATUS_SUSPENDED
            user.save()
            AuditLog.objects.create(user=request.user, action=f'Suspended user {user.email}', model_name='User', object_id=str(pk))
            messages.warning(request, f'{user.email} suspended.')
        elif action == 'activate':
            user.account_status = User.STATUS_ACTIVE
            user.save()
            AuditLog.objects.create(user=request.user, action=f'Activated user {user.email}', model_name='User', object_id=str(pk))
            messages.success(request, f'{user.email} activated.')
    return redirect('admin_users')


@login_required
def admin_bookings(request):
    if not request.user.is_platform_admin:
        return redirect('dashboard')
    from bookings.models import Booking
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.select_related(
        'facility', 'facility__institution', 'organization'
    ).order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    from django.core.paginator import Paginator
    page_obj = Paginator(bookings, 20).get_page(request.GET.get('page'))
    return render(request, 'dashboards/admin_bookings.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': __import__('bookings.models', fromlist=['Booking']).Booking.STATUS_CHOICES,
    })

def faq(request):
    faqs = [
        {'q': 'What is Campus After Dark?', 'a': 'Campus After Dark is a marketplace connecting educational institutions with organizations that want to book campus facilities like auditoriums, labs, and sports grounds.'},
        {'q': 'How does institution verification work?', 'a': 'After registration, institutions submit their documents. Our admin team reviews and approves within 24-48 hours. Approved institutions can then create and publish facilities.'},
        {'q': 'What is the platform commission?', 'a': 'Campus After Dark charges a configurable commission on each booking (currently 10%). This is shown transparently to both parties before any payment is made.'},
        {'q': 'Is payment secure?', 'a': 'The platform currently uses a demo payment simulation for testing. Integration with Razorpay for real payments requires configuring API credentials (see SETUP.md).'},
        {'q': 'Can I cancel a booking?', 'a': 'Yes. Bookings can be cancelled before they are confirmed. Once confirmed, cancellation policies set by the institution apply. All cancellations are recorded with reasons.'},
        {'q': 'How do I list my facility?', 'a': 'Register as an institution, get verified by our admin team, then create a facility listing from your dashboard. Set pricing, availability, and upload photos.'},
        {'q': 'What types of facilities can be listed?', 'a': 'Auditoriums, classrooms, computer labs, sports grounds, indoor sports halls, parking spaces, multipurpose halls, libraries, cafeterias, and more.'},
        {'q': 'Is the platform available across India?', 'a': 'Yes. The platform supports all Indian states and cities. Pricing is in INR and the timezone is Asia/Kolkata.'},
    ]
    return render(request, 'public/faq.html', {'faqs': faqs})

