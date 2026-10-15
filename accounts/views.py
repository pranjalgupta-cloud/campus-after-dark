from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, InstitutionProfile, OrganizationProfile, InstitutionDocument
from .forms import (
    LoginForm, InstitutionRegisterForm, OrganizationRegisterForm,
    InstitutionProfileForm, OrganizationProfileForm, DocumentUploadForm
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.account_status == User.STATUS_SUSPENDED:
                messages.error(request, 'Your account has been suspended. Contact support.')
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def register_choice(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/register_choice.html')


def register_institution(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = InstitutionRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone = form.cleaned_data['phone']
            user.role = User.ROLE_INSTITUTION
            user.save()
            InstitutionProfile.objects.create(
                user=user,
                name=form.cleaned_data['institution_name'],
                institution_type=form.cleaned_data['institution_type'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
            )
            login(request, user)
            messages.success(request, 'Account created! Please complete your institution profile and upload verification documents.')
            return redirect('institution_setup')
    else:
        form = InstitutionRegisterForm()
    return render(request, 'accounts/register_institution.html', {'form': form})


def register_organization(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = OrganizationRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone = form.cleaned_data['phone']
            user.role = User.ROLE_ORGANIZATION
            user.save()
            OrganizationProfile.objects.create(
                user=user,
                name=form.cleaned_data['org_name'],
                org_type=form.cleaned_data['org_type'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
            )
            login(request, user)
            messages.success(request, 'Account created! You can now explore and book facilities.')
            return redirect('dashboard')
    else:
        form = OrganizationRegisterForm()
    return render(request, 'accounts/register_organization.html', {'form': form})


@login_required
def institution_setup(request):
    """Institution profile completion and document upload"""
    if not request.user.is_institution:
        return redirect('dashboard')
    try:
        profile = request.user.institution_profile
    except InstitutionProfile.DoesNotExist:
        return redirect('dashboard')

    profile_form = InstitutionProfileForm(instance=profile)
    doc_form = DocumentUploadForm()

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            profile_form = InstitutionProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('institution_setup')
        elif 'upload_doc' in request.POST:
            doc_form = DocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.institution = profile
                doc.save()
                messages.success(request, 'Document uploaded successfully.')
                return redirect('institution_setup')

    documents = profile.documents.all()
    return render(request, 'accounts/institution_setup.html', {
        'profile': profile,
        'profile_form': profile_form,
        'doc_form': doc_form,
        'documents': documents,
    })


@login_required
def dashboard(request):
    """Route to appropriate dashboard by role"""
    user = request.user
    if user.is_platform_admin:
        return redirect('admin_dashboard')
    elif user.is_institution:
        return redirect('institution_dashboard')
    else:
        return redirect('org_dashboard')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Update basic user info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()

        if user.is_institution:
            try:
                prof = user.institution_profile
                form = InstitutionProfileForm(request.POST, request.FILES, instance=prof)
                if form.is_valid():
                    form.save()
            except InstitutionProfile.DoesNotExist:
                pass
        elif user.is_org:
            try:
                prof = user.org_profile
                form = OrganizationProfileForm(request.POST, request.FILES, instance=prof)
                if form.is_valid():
                    form.save()
            except OrganizationProfile.DoesNotExist:
                pass

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    context = {'user': user}
    if user.is_institution:
        try:
            context['institution_profile'] = user.institution_profile
            context['profile_form'] = InstitutionProfileForm(instance=user.institution_profile)
        except InstitutionProfile.DoesNotExist:
            pass
    elif user.is_org:
        try:
            context['org_profile'] = user.org_profile
            context['profile_form'] = OrganizationProfileForm(instance=user.org_profile)
        except OrganizationProfile.DoesNotExist:
            pass
    return render(request, 'accounts/profile.html', context)
