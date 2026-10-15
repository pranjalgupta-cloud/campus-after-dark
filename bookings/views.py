from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST
from decimal import Decimal
import datetime, json

from .models import Booking, BookingStatusHistory, Payment, Payout, Review, Notification, PlatformSetting
from .forms import BookingRequestForm, ReviewForm
from facilities.models import Facility
from accounts.models import OrganizationProfile, InstitutionProfile


def _create_notification(user, notif_type, title, message, booking=None):
    Notification.objects.create(
        user=user,
        notification_type=notif_type,
        title=title,
        message=message,
        related_booking=booking
    )


def _log_status_change(booking, from_status, to_status, user=None, note=''):
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status=from_status,
        to_status=to_status,
        changed_by=user,
        note=note
    )


def check_availability(facility, booked_date, start_time, end_time, exclude_booking_id=None):
    """Returns True if the slot is available, False if conflicting booking exists."""
    qs = Booking.objects.filter(
        facility=facility,
        booked_date=booked_date,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_APPROVED, Booking.STATUS_PENDING]
    )
    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)
    for b in qs:
        # Check overlap: new booking overlaps if start < existing end AND end > existing start
        if start_time < b.end_time and end_time > b.start_time:
            return False
    return True


@login_required
def request_booking(request, facility_pk):
    """Organization: submit a booking request"""
    if not request.user.is_org:
        messages.error(request, 'Only organizations can make booking requests.')
        return redirect('facility_detail', pk=facility_pk)

    facility = get_object_or_404(
        Facility, pk=facility_pk, status=Facility.STATUS_PUBLISHED,
        institution__verification_status=InstitutionProfile.STATUS_APPROVED
    )

    try:
        org_profile = request.user.org_profile
    except OrganizationProfile.DoesNotExist:
        messages.error(request, 'Please complete your organization profile first.')
        return redirect('profile')

    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booked_date = form.cleaned_data['booked_date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            attendee_count = form.cleaned_data['attendee_count']

            # Validate capacity
            if attendee_count > facility.capacity:
                messages.error(request, f'Attendee count exceeds facility capacity of {facility.capacity}.')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            # Validate operating hours
            if start_time < facility.opening_time or end_time > facility.closing_time:
                messages.error(request, f'Booking must be within operating hours: {facility.opening_time.strftime("%I:%M %p")} – {facility.closing_time.strftime("%I:%M %p")}')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            # Validate blocked dates
            if facility.blocked_dates.filter(blocked_date=booked_date).exists():
                messages.error(request, 'This date is blocked by the institution.')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            # Validate day of week
            day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
            weekday = day_map[booked_date.weekday()]
            available_days = [d.strip() for d in facility.available_days.split(',')]
            if weekday not in available_days:
                messages.error(request, f'Facility is not available on {booked_date.strftime("%A")}s.')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            # Check availability (backend conflict check)
            if not check_availability(facility, booked_date, start_time, end_time):
                messages.error(request, 'This time slot is already booked. Please choose a different time.')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            # Calculate price
            dt_start = datetime.datetime.combine(booked_date, start_time)
            dt_end = datetime.datetime.combine(booked_date, end_time)
            hours = Decimal(str((dt_end - dt_start).total_seconds() / 3600))

            if hours < facility.min_booking_hours:
                messages.error(request, f'Minimum booking duration is {facility.min_booking_hours} hour(s).')
                return render(request, 'bookings/request.html', {'form': form, 'facility': facility})

            price_per_hour = facility.price_per_unit
            subtotal = (price_per_hour * hours).quantize(Decimal('0.01'))
            commission_rate = PlatformSetting.get_commission_rate()
            commission_amount = (subtotal * commission_rate / 100).quantize(Decimal('0.01'))
            institution_payout = subtotal - commission_amount

            with transaction.atomic():
                booking = Booking.objects.create(
                    facility=facility,
                    organization=org_profile,
                    booked_date=booked_date,
                    start_time=start_time,
                    end_time=end_time,
                    attendee_count=attendee_count,
                    purpose=form.cleaned_data['purpose'],
                    additional_requirements=form.cleaned_data['additional_requirements'],
                    hours_booked=hours,
                    price_per_hour=price_per_hour,
                    subtotal=subtotal,
                    commission_rate=commission_rate,
                    commission_amount=commission_amount,
                    institution_payout=institution_payout,
                    total_amount=subtotal,
                    status=Booking.STATUS_PENDING,
                )
                _log_status_change(booking, '', Booking.STATUS_PENDING, request.user, 'Booking request submitted')

                # Notify institution
                _create_notification(
                    facility.institution.user,
                    'booking_request',
                    f'New Booking Request — {facility.name}',
                    f'{org_profile.name} has requested {facility.name} on {booked_date.strftime("%d %b %Y")} from {start_time.strftime("%I:%M %p")} to {end_time.strftime("%I:%M %p")}.',
                    booking=booking
                )

            messages.success(request, f'Booking request submitted! Reference: {booking.reference_number}')
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = BookingRequestForm()

    return render(request, 'bookings/request.html', {'form': form, 'facility': facility})


@login_required
def booking_detail(request, pk):
    """View booking detail — org sees own, institution sees their facility's"""
    booking = get_object_or_404(Booking, pk=pk)
    user = request.user

    # Authorization
    if user.is_org:
        if booking.organization.user != user:
            messages.error(request, 'Access denied.')
            return redirect('org_dashboard')
    elif user.is_institution:
        if booking.facility.institution.user != user:
            messages.error(request, 'Access denied.')
            return redirect('institution_dashboard')
    elif not user.is_platform_admin:
        return redirect('dashboard')

    review_form = None
    existing_review = None
    if booking.status == Booking.STATUS_COMPLETED and user.is_org:
        try:
            existing_review = booking.review
        except Review.DoesNotExist:
            review_form = ReviewForm()

    return render(request, 'bookings/detail.html', {
        'booking': booking,
        'review_form': review_form,
        'existing_review': existing_review,
        'history': booking.status_history.all(),
    })


@login_required
@require_POST
def approve_booking(request, pk):
    """Institution: approve a booking request"""
    if not request.user.is_institution:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    booking = get_object_or_404(
        Booking, pk=pk,
        facility__institution__user=request.user,
        status=Booking.STATUS_PENDING
    )
    old_status = booking.status
    booking.status = Booking.STATUS_APPROVED
    booking.save()
    _log_status_change(booking, old_status, Booking.STATUS_APPROVED, request.user, 'Approved by institution')

    _create_notification(
        booking.organization.user,
        'booking_approved',
        f'Booking Approved — {booking.facility.name}',
        f'Your booking request ({booking.reference_number}) has been approved! Please complete payment to confirm.',
        booking=booking
    )
    messages.success(request, f'Booking {booking.reference_number} approved. Organization will be notified to pay.')
    return redirect('institution_bookings')


@login_required
@require_POST
def reject_booking(request, pk):
    """Institution: reject a booking request"""
    if not request.user.is_institution:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    booking = get_object_or_404(
        Booking, pk=pk,
        facility__institution__user=request.user,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_APPROVED]
    )
    reason = request.POST.get('reason', '').strip()
    old_status = booking.status
    booking.status = Booking.STATUS_REJECTED
    booking.rejection_reason = reason
    booking.save()
    _log_status_change(booking, old_status, Booking.STATUS_REJECTED, request.user, reason or 'Rejected by institution')

    _create_notification(
        booking.organization.user,
        'booking_rejected',
        f'Booking Rejected — {booking.facility.name}',
        f'Your booking request ({booking.reference_number}) was rejected. Reason: {reason or "Not provided"}',
        booking=booking
    )
    messages.success(request, f'Booking {booking.reference_number} rejected.')
    return redirect('institution_bookings')


@login_required
@require_POST
def cancel_booking(request, pk):
    """Org or institution cancels a booking"""
    booking = get_object_or_404(Booking, pk=pk)
    user = request.user

    # Authorization
    is_org_owner = user.is_org and booking.organization.user == user
    is_institution_owner = user.is_institution and booking.facility.institution.user == user
    if not (is_org_owner or is_institution_owner or user.is_platform_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if booking.status not in [Booking.STATUS_PENDING, Booking.STATUS_APPROVED, Booking.STATUS_CONFIRMED]:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking_detail', pk=pk)

    reason = request.POST.get('reason', '').strip()
    old_status = booking.status
    booking.status = Booking.STATUS_CANCELLED
    booking.cancellation_reason = reason
    booking.cancelled_by = user
    booking.save()
    _log_status_change(booking, old_status, Booking.STATUS_CANCELLED, user, reason or 'Cancelled')

    # Notify the other party
    if is_org_owner:
        _create_notification(
            booking.facility.institution.user, 'booking_cancelled',
            f'Booking Cancelled — {booking.facility.name}',
            f'Booking {booking.reference_number} was cancelled by the organization.',
            booking=booking
        )
    else:
        _create_notification(
            booking.organization.user, 'booking_cancelled',
            f'Booking Cancelled — {booking.facility.name}',
            f'Your booking {booking.reference_number} was cancelled. Reason: {reason or "Not provided"}',
            booking=booking
        )

    messages.success(request, f'Booking {booking.reference_number} cancelled.')
    return redirect('booking_detail', pk=pk)


@login_required
def payment_page(request, pk):
    """Demo payment page — clearly labelled as demo"""
    if not request.user.is_org:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    booking = get_object_or_404(
        Booking, pk=pk,
        organization__user=request.user,
        status=Booking.STATUS_APPROVED
    )
    return render(request, 'bookings/payment.html', {'booking': booking})


@login_required
@require_POST
def process_payment(request, pk):
    """Demo payment processor — simulates success/failure"""
    if not request.user.is_org:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    booking = get_object_or_404(
        Booking, pk=pk,
        organization__user=request.user,
        status=Booking.STATUS_APPROVED
    )
    simulate_failure = request.POST.get('simulate_failure') == '1'

    with transaction.atomic():
        import uuid as _uuid
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            method=Payment.METHOD_DEMO,
            status=Payment.STATUS_FAILED if simulate_failure else Payment.STATUS_SUCCESS,
            provider_reference=f'DEMO-{_uuid.uuid4().hex[:12].upper()}',
            paid_at=timezone.now() if not simulate_failure else None,
        )
        if not simulate_failure:
            old_status = booking.status
            booking.status = Booking.STATUS_CONFIRMED
            booking.save()
            _log_status_change(booking, old_status, Booking.STATUS_CONFIRMED, request.user, 'Payment completed (demo)')

            # Create payout record
            Payout.objects.create(
                booking=booking,
                institution=booking.facility.institution,
                amount=booking.institution_payout,
            )

            _create_notification(
                booking.facility.institution.user, 'payment_received',
                f'Payment Received — {booking.facility.name}',
                f'Payment of ₹{booking.total_amount} received for booking {booking.reference_number}.',
                booking=booking
            )
            _create_notification(
                booking.organization.user, 'booking_confirmed',
                f'Booking Confirmed — {booking.facility.name}',
                f'Your booking {booking.reference_number} is confirmed!',
                booking=booking
            )
            messages.success(request, f'Payment successful! Booking {booking.reference_number} is confirmed.')
            return redirect('booking_detail', pk=pk)
        else:
            old_status = booking.status
            booking.status = Booking.STATUS_PAYMENT_FAILED
            booking.save()
            _log_status_change(booking, old_status, Booking.STATUS_PAYMENT_FAILED, request.user, 'Demo payment failed')
            messages.error(request, 'Payment simulation failed. Please try again.')
            return redirect('payment_page', pk=pk)


@login_required
@require_POST
def submit_review(request, pk):
    """Org: submit review for a completed booking"""
    booking = get_object_or_404(
        Booking, pk=pk,
        organization__user=request.user,
        status=Booking.STATUS_COMPLETED
    )
    try:
        booking.review
        messages.info(request, 'You have already reviewed this booking.')
        return redirect('booking_detail', pk=pk)
    except Review.DoesNotExist:
        pass

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.booking = booking
        review.facility = booking.facility
        review.reviewer = request.user
        review.save()
        messages.success(request, 'Review submitted. Thank you!')
    else:
        messages.error(request, 'Invalid review data.')
    return redirect('booking_detail', pk=pk)


@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ─── Institution booking management ─────────────────────────────────────────

@login_required
def institution_bookings(request):
    if not request.user.is_institution:
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except Exception:
        return redirect('institution_setup')

    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(
        facility__institution=profile
    ).select_related('facility', 'organization', 'organization__user').order_by('-created_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = __import__('django.core.paginator', fromlist=['Paginator']).Paginator(bookings, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'bookings/institution_bookings.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    })


# ─── Organization booking list ───────────────────────────────────────────────

@login_required
def org_bookings(request):
    if not request.user.is_org:
        return redirect('dashboard')
    try:
        org = request.user.org_profile
    except Exception:
        return redirect('profile')

    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(
        organization=org
    ).select_related('facility', 'facility__institution').order_by('-created_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = __import__('django.core.paginator', fromlist=['Paginator']).Paginator(bookings, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'bookings/org_bookings.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    })


@login_required
def mark_booking_completed(request, pk):
    """Institution: mark a confirmed past booking as completed"""
    if not request.user.is_institution:
        return redirect('dashboard')
    booking = get_object_or_404(
        Booking, pk=pk,
        facility__institution__user=request.user,
        status=Booking.STATUS_CONFIRMED
    )
    if booking.booked_date <= timezone.now().date():
        old = booking.status
        booking.status = Booking.STATUS_COMPLETED
        booking.save()
        _log_status_change(booking, old, Booking.STATUS_COMPLETED, request.user, 'Marked completed')
        messages.success(request, 'Booking marked as completed.')
    else:
        messages.error(request, 'Cannot complete a future booking.')
    return redirect('booking_detail', pk=pk)
