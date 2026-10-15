from django import forms
from .models import Booking, Review


class BookingRequestForm(forms.Form):
    booked_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_booked_date'}),
        label='Booking Date'
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'id_start_time'}),
        label='Start Time'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'id_end_time'}),
        label='End Time'
    )
    attendee_count = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of attendees'}),
        label='Expected Attendees'
    )
    purpose = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Purpose of booking'}),
        label='Purpose'
    )
    additional_requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special requirements...'}),
        label='Additional Requirements'
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        date = cleaned_data.get('booked_date')
        import datetime
        if start and end and start >= end:
            raise forms.ValidationError('End time must be after start time.')
        if date and date < datetime.date.today():
            raise forms.ValidationError('Booking date cannot be in the past.')
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Share your experience with this facility...'
            }),
        }
