from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, InstitutionProfile, OrganizationProfile, InstitutionDocument


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Email address',
            'autofocus': True
        }),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password'
        })
    )


class InstitutionRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXX XXXXX'}))
    institution_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Institution Name'}))
    institution_type = forms.ChoiceField(
        choices=[
            ('', 'Select Type'),
            ('university', 'University'),
            ('college', 'College / Degree College'),
            ('engineering', 'Engineering Institute'),
            ('management', 'Management Institute'),
            ('school', 'School'),
            ('polytechnic', 'Polytechnic'),
            ('research', 'Research Institute'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    state = forms.ChoiceField(
        choices=[('', 'Select State')] + [
            ('Andhra Pradesh', 'Andhra Pradesh'), ('Assam', 'Assam'),
            ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'),
            ('Delhi', 'Delhi'), ('Goa', 'Goa'), ('Gujarat', 'Gujarat'),
            ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'),
            ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'),
            ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'),
            ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'),
            ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'),
            ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'),
            ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'),
            ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'),
            ('Telangana', 'Telangana'), ('Tripura', 'Tripura'),
            ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'),
            ('West Bengal', 'West Bengal'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    agree_terms = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class OrganizationRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXX XXXXX'}))
    org_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization Name'}))
    org_type = forms.ChoiceField(
        choices=[
            ('', 'Select Type'),
            ('business', 'Business'),
            ('ngo', 'NGO / Non-profit'),
            ('sports', 'Sports Club'),
            ('event', 'Event Organizer'),
            ('training', 'Training Provider'),
            ('government', 'Government Body'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    state = forms.ChoiceField(
        choices=[('', 'Select State')] + [
            ('Andhra Pradesh', 'Andhra Pradesh'), ('Assam', 'Assam'),
            ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'),
            ('Delhi', 'Delhi'), ('Goa', 'Goa'), ('Gujarat', 'Gujarat'),
            ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'),
            ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'),
            ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'),
            ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'),
            ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'),
            ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'),
            ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'),
            ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'),
            ('Telangana', 'Telangana'), ('Tripura', 'Tripura'),
            ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'),
            ('West Bengal', 'West Bengal'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    agree_terms = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class InstitutionProfileForm(forms.ModelForm):
    class Meta:
        model = InstitutionProfile
        fields = ['name', 'institution_type', 'registration_number', 'address', 'city', 'state', 'pincode', 'website', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'institution_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class OrganizationProfileForm(forms.ModelForm):
    class Meta:
        model = OrganizationProfile
        fields = ['name', 'org_type', 'registration_number', 'gst_number', 'address', 'city', 'state', 'pincode', 'website', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'org_type': forms.Select(attrs={'class': 'form-select'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = InstitutionDocument
        fields = ['doc_type', 'title', 'file']
        widgets = {
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document title'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
