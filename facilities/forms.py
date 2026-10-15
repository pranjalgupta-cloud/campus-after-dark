from django import forms
from .models import Facility, FacilityImage, BlockedDate, AvailabilityRule


INDIAN_CITIES = [
    ('', 'Select City'),
    ('Mumbai', 'Mumbai'), ('Delhi', 'Delhi'), ('Bengaluru', 'Bengaluru'),
    ('Hyderabad', 'Hyderabad'), ('Chennai', 'Chennai'), ('Kolkata', 'Kolkata'),
    ('Pune', 'Pune'), ('Ahmedabad', 'Ahmedabad'), ('Jaipur', 'Jaipur'),
    ('Lucknow', 'Lucknow'), ('Kanpur', 'Kanpur'), ('Nagpur', 'Nagpur'),
    ('Visakhapatnam', 'Visakhapatnam'), ('Bhopal', 'Bhopal'), ('Patna', 'Patna'),
    ('Ludhiana', 'Ludhiana'), ('Agra', 'Agra'), ('Nashik', 'Nashik'),
    ('Faridabad', 'Faridabad'), ('Meerut', 'Meerut'), ('Indore', 'Indore'),
    ('Vadodara', 'Vadodara'), ('Surat', 'Surat'), ('Coimbatore', 'Coimbatore'),
    ('Kochi', 'Kochi'), ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Mysuru', 'Mysuru'), ('Chandigarh', 'Chandigarh'), ('Guwahati', 'Guwahati'),
    ('Bhubaneswar', 'Bhubaneswar'), ('Raipur', 'Raipur'), ('Other', 'Other'),
]


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        exclude = ['institution', 'status', 'is_featured', 'view_count', 'created_at', 'updated_at', 'amenities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Facility name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe this facility...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN Code'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 19.0760'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 72.8777'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max capacity'}),
            'pricing_model': forms.Select(attrs={'class': 'form-select'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in ₹'}),
            'min_booking_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_booking_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rules and restrictions...'}),
            'permitted_activities': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Permitted activities...'}),
            'opening_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mon,Tue,Wed,Thu,Fri,Sat'}),
        }


class FacilitySearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search facilities...'}),
        label='Search'
    )
    city = forms.ChoiceField(
        choices=INDIAN_CITIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='City'
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Facility.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Category'
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date'
    )
    min_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min capacity'}),
        label='Min Capacity'
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max ₹/hour'}),
        label='Max Price/Hour'
    )
    sort = forms.ChoiceField(
        choices=[
            ('', 'Relevance'),
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('capacity_desc', 'Capacity: High to Low'),
            ('newest', 'Newest First'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sort By'
    )


class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ['blocked_date', 'reason']
        widgets = {
            'blocked_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason (optional)'}),
        }
