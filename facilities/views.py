from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.utils import timezone
from .models import Facility, FacilityImage, Amenity, FacilityAmenity, BlockedDate
from .forms import FacilityForm, FacilitySearchForm, BlockedDateForm
from accounts.models import InstitutionProfile
import datetime


def explore(request):
    """Public facility search and listing page"""
    form = FacilitySearchForm(request.GET)
    facilities = Facility.objects.filter(
        status=Facility.STATUS_PUBLISHED,
        institution__verification_status=InstitutionProfile.STATUS_APPROVED
    ).select_related('institution').prefetch_related('images')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        city = form.cleaned_data.get('city')
        category = form.cleaned_data.get('category')
        min_capacity = form.cleaned_data.get('min_capacity')
        max_price = form.cleaned_data.get('max_price')
        sort = form.cleaned_data.get('sort')

        if q:
            facilities = facilities.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(city__icontains=q) |
                Q(institution__name__icontains=q)
            )
        if city:
            facilities = facilities.filter(city__icontains=city)
        if category:
            facilities = facilities.filter(category=category)
        if min_capacity:
            facilities = facilities.filter(capacity__gte=min_capacity)
        if max_price:
            facilities = facilities.filter(price_per_unit__lte=max_price)
        if sort == 'price_asc':
            facilities = facilities.order_by('price_per_unit')
        elif sort == 'price_desc':
            facilities = facilities.order_by('-price_per_unit')
        elif sort == 'capacity_desc':
            facilities = facilities.order_by('-capacity')
        elif sort == 'newest':
            facilities = facilities.order_by('-created_at')

    paginator = Paginator(facilities, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'facilities/explore.html', {
        'form': form,
        'page_obj': page_obj,
        'total_count': facilities.count(),
        'categories': Facility.CATEGORY_CHOICES,
    })


def facility_detail(request, pk):
    """Public facility detail page"""
    facility = get_object_or_404(
        Facility,
        pk=pk,
        status=Facility.STATUS_PUBLISHED,
        institution__verification_status=InstitutionProfile.STATUS_APPROVED
    )
    # Increment view count
    Facility.objects.filter(pk=pk).update(view_count=facility.view_count + 1)

    reviews = facility.reviews.filter(is_visible=True).select_related('reviewer').order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    blocked_dates = list(facility.blocked_dates.values_list('blocked_date', flat=True))
    blocked_dates_str = [d.strftime('%Y-%m-%d') for d in blocked_dates]

    # Get confirmed bookings to show busy slots
    from bookings.models import Booking
    confirmed_bookings = Booking.objects.filter(
        facility=facility,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_APPROVED],
        booked_date__gte=timezone.now().date()
    ).values('booked_date', 'start_time', 'end_time')

    return render(request, 'facilities/detail.html', {
        'facility': facility,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': reviews.count(),
        'blocked_dates': blocked_dates_str,
        'confirmed_bookings': list(confirmed_bookings),
        'amenities': facility.amenities.all(),
    })


# ─── Institution facility management ────────────────────────────────────────

@login_required
def institution_facilities(request):
    """Institution: list own facilities"""
    if not request.user.is_institution:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return redirect('institution_setup')

    facilities = Facility.objects.filter(institution=profile).order_by('-created_at')
    return render(request, 'facilities/institution_list.html', {
        'facilities': facilities,
        'institution': profile,
    })


@login_required
def facility_create(request):
    """Institution: create a new facility"""
    if not request.user.is_institution:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return redirect('institution_setup')

    if not profile.is_verified:
        messages.warning(request, 'Your institution must be verified before creating facilities.')
        return redirect('institution_setup')

    if request.method == 'POST':
        form = FacilityForm(request.POST)
        if form.is_valid():
            facility = form.save(commit=False)
            facility.institution = profile
            facility.save()
            # Handle amenities
            amenity_ids = request.POST.getlist('amenities')
            for aid in amenity_ids:
                try:
                    amenity = Amenity.objects.get(pk=aid)
                    FacilityAmenity.objects.get_or_create(facility=facility, amenity=amenity)
                except Amenity.DoesNotExist:
                    pass
            # Handle images
            images = request.FILES.getlist('images')
            for i, img in enumerate(images[:10]):
                FacilityImage.objects.create(
                    facility=facility,
                    image=img,
                    is_primary=(i == 0),
                    order=i
                )
            messages.success(request, f'Facility "{facility.name}" created! Set status to Published when ready.')
            return redirect('facility_edit', pk=facility.pk)
    else:
        form = FacilityForm()

    amenities = Amenity.objects.all()
    return render(request, 'facilities/facility_form.html', {
        'form': form,
        'amenities': amenities,
        'action': 'Create',
    })


@login_required
def facility_edit(request, pk):
    """Institution: edit a facility"""
    if not request.user.is_institution:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return redirect('institution_setup')

    facility = get_object_or_404(Facility, pk=pk, institution=profile)

    if request.method == 'POST':
        form = FacilityForm(request.POST, instance=facility)
        if form.is_valid():
            form.save()
            # Update amenities
            FacilityAmenity.objects.filter(facility=facility).delete()
            for aid in request.POST.getlist('amenities'):
                try:
                    amenity = Amenity.objects.get(pk=aid)
                    FacilityAmenity.objects.create(facility=facility, amenity=amenity)
                except Amenity.DoesNotExist:
                    pass
            # Add new images
            for i, img in enumerate(request.FILES.getlist('images')[:10]):
                count = facility.images.count()
                FacilityImage.objects.create(facility=facility, image=img, order=count + i)
            messages.success(request, 'Facility updated successfully.')
            return redirect('facility_edit', pk=pk)
    else:
        form = FacilityForm(instance=facility)

    blocked_date_form = BlockedDateForm()
    blocked_dates = facility.blocked_dates.all()
    amenities = Amenity.objects.all()
    selected_amenity_ids = list(facility.amenities.values_list('id', flat=True))

    return render(request, 'facilities/facility_form.html', {
        'form': form,
        'facility': facility,
        'amenities': amenities,
        'selected_amenity_ids': [str(a) for a in selected_amenity_ids],
        'blocked_date_form': blocked_date_form,
        'blocked_dates': blocked_dates,
        'images': facility.images.all(),
        'action': 'Edit',
    })


@login_required
def facility_toggle_status(request, pk):
    """Institution: publish/unpublish/deactivate a facility"""
    if not request.user.is_institution:
        return JsonResponse({'error': 'Access denied'}, status=403)
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)

    facility = get_object_or_404(Facility, pk=pk, institution=profile)
    new_status = request.POST.get('status')
    if new_status in [Facility.STATUS_PUBLISHED, Facility.STATUS_DRAFT, Facility.STATUS_INACTIVE]:
        if new_status == Facility.STATUS_PUBLISHED and not profile.is_verified:
            messages.error(request, 'Institution must be verified to publish facilities.')
            return redirect('institution_facilities')
        facility.status = new_status
        facility.save()
        messages.success(request, f'Facility status changed to {facility.get_status_display()}.')
    return redirect('institution_facilities')


@login_required
def add_blocked_date(request, pk):
    """Institution: block a date for a facility"""
    if not request.user.is_institution:
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return redirect('institution_setup')

    facility = get_object_or_404(Facility, pk=pk, institution=profile)
    if request.method == 'POST':
        form = BlockedDateForm(request.POST)
        if form.is_valid():
            bd = form.save(commit=False)
            bd.facility = facility
            try:
                bd.save()
                messages.success(request, f'{bd.blocked_date} blocked successfully.')
            except Exception:
                messages.error(request, 'That date is already blocked.')
    return redirect('facility_edit', pk=pk)


@login_required
def remove_blocked_date(request, pk, date_pk):
    """Institution: unblock a date"""
    if not request.user.is_institution:
        return redirect('dashboard')
    blocked = get_object_or_404(BlockedDate, pk=date_pk, facility__pk=pk,
                                 facility__institution__user=request.user)
    blocked.delete()
    messages.success(request, 'Date unblocked.')
    return redirect('facility_edit', pk=pk)


@login_required
def delete_facility_image(request, pk, image_pk):
    """Institution: delete a facility image"""
    if not request.user.is_institution:
        return redirect('dashboard')
    image = get_object_or_404(
        FacilityImage, pk=image_pk, facility__pk=pk,
        facility__institution__user=request.user
    )
    image.image.delete(save=False)
    image.delete()
    messages.success(request, 'Image removed.')
    return redirect('facility_edit', pk=pk)
