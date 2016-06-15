from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms.formsets import formset_factory
from djangoformsetjs.utils import formset_media_js

from dataloader.models import SamplingFeature, Action, People, Organization, Affiliation, Result, ActionBy, Method


# AUTHORIZATION
class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit)
        if user:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if commit:
                user.save()
        return user


# ODM2
class SamplingFeatureForm(forms.ModelForm):
    class Meta:
        model = SamplingFeature
        fields = [
            'sampling_feature_code',
            'sampling_feature_name',
            'sampling_feature_description',
            'elevation_m',
            'elevation_datum',
        ]


class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            'method',
        ]


class MethodForm(forms.ModelForm):
    class Meta:
        model = Method
        fields = [
            'method_code',
            'method_name',
            'method_description',
        ]


class ActionByForm(forms.ModelForm):
    class Meta:
        model = ActionBy
        fields = [
            'is_action_lead',
            'role_description',
        ]


class PeopleForm(forms.ModelForm):
    class Meta:
        model = People
        fields = [
            'person_first_name',
            'person_middle_name',
            'person_last_name',
        ]


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'organization_code',
            'organization_name',
            'organization_description',
        ]


class AffiliationForm(forms.ModelForm):
    class Meta:
        model = Affiliation
        fields = [
            'is_primary_organization_contact',
            'affiliation_start_date',
            'primary_phone',
            'primary_email',
            'primary_address',
        ]


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = [
            'variable',
            'unit',
            'sampled_medium',
        ]

    class Media(object):
        js = formset_media_js + ()

ResultFormSet = formset_factory(ResultForm)
