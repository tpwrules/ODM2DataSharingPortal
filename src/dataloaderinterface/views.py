# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from uuid import uuid4
import json
import requests
import re
import logging
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from django.conf import settings
from django.db.models.aggregates import Max
from django.db.models.expressions import F
from django.db.models.query import Prefetch
from django.utils.safestring import mark_safe

from dataloaderservices.views import CSVDataApi

from dataloader.models import FeatureAction, Result, ProcessingLevel, TimeSeriesResult, SamplingFeature, \
    SpatialReference, \
    ElevationDatum, SiteType, ActionBy, Action, Method, DataLoggerProgramFile, DataLoggerFile, \
    InstrumentOutputVariable, DataLoggerFileColumn, TimeSeriesResultValue
from leafpack.models import LeafPack, LeafPackBug, Macroinvertebrate
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseRedirect, Http404, HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView, ModelFormMixin
from django.views.generic.list import ListView
from django.core.management import call_command

from dataloaderinterface.forms import SamplingFeatureForm, ResultFormSet, SiteForm, \
    OrganizationForm, ActionByForm, HydroShareSettingsForm, SiteAlertForm, \
    HydroShareResourceDeleteForm, SiteRegistrationForm, SiteSensorForm
from dataloaderinterface.models import ODM2User, SiteRegistration, SiteSensor, SiteAlert
from hydroshare.models import HydroShareResource, HydroShareAccount, OAuthToken
from hydroshare_util import HydroShareNotFound, HydroShareHTTPException
from hydroshare_util.utility import HydroShareUtility
from hydroshare_util.adapter import HydroShareAdapter
from hydroshare_util.auth import AuthUtil
from hydroshare_util.resource import Resource
from hydroshare_util.coverage import PointCoverage, BoxCoverage, PeriodCoverage, Coverage
from accounts.models import User


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls):
        return login_required(super(LoginRequiredMixin, cls).as_view())


class HomeView(TemplateView):
    template_name = 'dataloaderinterface/home.html'


class SitesListView(LoginRequiredMixin, ListView):
    model = SiteRegistration
    context_object_name = 'sites'
    template_name = 'dataloaderinterface/my-sites.html'

    def get_queryset(self):
        return super(SitesListView, self).get_queryset()\
            .with_sensors()\
            .with_latest_measurement_id()\
            .deployed_by(user_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super(SitesListView, self).get_context_data()
        context['followed_sites'] = super(SitesListView, self).get_queryset()\
            .with_sensors() \
            .with_latest_measurement_id() \
            .followed_by(user_id=self.request.user.id)
        return context


class StatusListView(ListView):
    model = SiteRegistration
    context_object_name = 'sites'
    template_name = 'dataloaderinterface/status.html'

    def get_queryset(self):
        return super(StatusListView, self).get_queryset()\
            .with_status_sensors()\
            .deployed_by(self.request.user.id) \
            .with_latest_measurement_id() \
            .order_by('sampling_feature_code')

    def get_context_data(self, **kwargs):
        context = super(StatusListView, self).get_context_data(**kwargs)
        context['followed_sites'] = super(StatusListView, self).get_queryset()\
            .with_status_sensors()\
            .followed_by(user_id=self.request.user.id) \
            .with_latest_measurement_id() \
            .order_by('sampling_feature_code')
        return context


class BrowseSitesListView(ListView):
    model = SiteRegistration
    context_object_name = 'sites'
    template_name = 'dataloaderinterface/browse-sites.html'

    def get_queryset(self):
        return super(BrowseSitesListView, self).get_queryset()\
            .with_sensors()\
            .with_leafpacks()\
            .with_latest_measurement_id()\
            .with_ownership_status(self.request.user.id)


class SiteDetailView(DetailView):
    model = SiteRegistration
    context_object_name = 'site'
    slug_field = 'sampling_feature_code'
    slug_url_kwarg = 'sampling_feature_code'
    template_name = 'dataloaderinterface/site_details.html'

    def get_queryset(self):
        return super(SiteDetailView, self).get_queryset().with_sensors().with_sensors_last_measurement()

    def get_context_data(self, **kwargs):
        context = super(SiteDetailView, self).get_context_data(**kwargs)
        context['is_followed'] = self.object.followed_by.filter(id=self.request.user.id).exists()
        context['can_administer_site'] = self.request.user.can_administer_site(self.object)
        context['is_site_owner'] = self.request.user == self.object.django_user
        context['tsa_url'] = settings.TSA_URL

        context['leafpacks'] = LeafPack.objects.filter(site_registration=context['site'].pk)

        try:
            context["hydroshare_account"] = self.request.user.hydroshare_account
        except AttributeError:
            pass

        try:
            resources = HydroShareResource.objects.filter(site_registration=context['site'].pk)
            visible_resources = [res for res in resources if res.visible]
            context['resource_is_connected'] = len(visible_resources) > 0
        except ObjectDoesNotExist:
            pass

        return context


class SensorListUpdateView(DetailView):
    template_name = 'dataloaderinterface/manage_sensors.html'
    model = SiteRegistration
    slug_field = 'sampling_feature_code'
    slug_url_kwarg = 'sampling_feature_code'

    def dispatch(self, request, *args, **kwargs):
        site = SiteRegistration.objects.get(sampling_feature_code=self.kwargs['sampling_feature_code'])
        if not request.user.can_administer_site(site):
            raise Http404
        return super(SensorListUpdateView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super(SensorListUpdateView, self).get_queryset().with_sensors()

    def get_context_data(self, **kwargs):
        context = super(SensorListUpdateView, self).get_context_data(**kwargs)
        context['sensor_form'] = SiteSensorForm(initial={'registration': self.object.registration_id})
        return context


class LeafPackListUpdateView(DetailView):
    template_name = 'dataloaderinterface/manage_leafpack.html'
    model = SiteRegistration
    slug_field = 'sampling_feature_code'
    slug_url_kwarg = 'sampling_feature_code'

    def dispatch(self, request, *args, **kwargs):
        site = SiteRegistration.objects.get(sampling_feature_code=self.kwargs['sampling_feature_code'])
        if not request.user.can_administer_site(site):
            raise Http404
        return super(LeafPackListUpdateView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SiteRegistration.objects.with_leafpacks()

    def get_context_data(self, **kwargs):
        context = super(LeafPackListUpdateView, self).get_context_data(**kwargs)
        return context


class SiteDeleteView(LoginRequiredMixin, DeleteView):
    model = SiteRegistration
    slug_field = 'sampling_feature_code'
    slug_url_kwarg = 'sampling_feature_code'
    success_url = reverse_lazy('sites_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_administer_site(self.get_object()):
            raise Http404
        return super(SiteDeleteView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return redirect(reverse('site_detail', kwargs={'sampling_feature_code': self.get_object().sampling_feature_code}))

    def post(self, request, *args, **kwargs):
        site_registration = self.get_object()
        site_registration.delete()

        messages.success(request, 'The site has been deleted successfully.')
        return HttpResponseRedirect(self.success_url)


class SiteUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'dataloaderinterface/site_registration_update.html'
    slug_url_kwarg = 'sampling_feature_code'
    slug_field = 'sampling_feature_code'
    form_class = SiteRegistrationForm
    model = SiteRegistration
    object = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_administer_site(self.get_object()):
            raise Http404

        return super(SiteUpdateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('site_detail', kwargs={'sampling_feature_code': self.object.sampling_feature_code})

    def get_queryset(self):
        return super(SiteUpdateView, self).get_queryset().with_sensors()

    def get_hydroshare_accounts(self):
        try:
            return HydroShareAccount.objects.filter(user=self.request.user.id)
        except ObjectDoesNotExist:
            return []

    def get_context_data(self, **kwargs):
        data = self.request.POST or {}
        context = super(SiteUpdateView, self).get_context_data()

        site_alert = self.request.user.site_alerts\
            .filter(site_registration__sampling_feature_code=self.object.sampling_feature_code)\
            .first()

        alert_data = {'notify': True, 'hours_threshold': int(site_alert.hours_threshold.total_seconds() / 3600)} \
            if site_alert \
            else {}

        # maybe just access site.leafpacks in the template? Naw.
        context['leafpacks'] = LeafPack.objects.filter(site_registration=self.object)
        context['sensor_form'] = SiteSensorForm(initial={'registration': self.object.registration_id})
        context['email_alert_form'] = SiteAlertForm(data=alert_data)
        context['zoom_level'] = data['zoom-level'] if 'zoom-level' in data else None

        return context

    def post(self, request, *args, **kwargs):
        site_registration = self.get_object()
        form = self.get_form_class()(request.POST, instance=site_registration)
        notify_form = SiteAlertForm(request.POST)

        if form.is_valid() and notify_form.is_valid():
            form.instance.affiliation_id = form.cleaned_data['affiliation_id'] or request.user.affiliation_id

            site_alert = self.request.user.site_alerts.filter(site_registration=site_registration).first()

            if notify_form.cleaned_data['notify'] and site_alert:
                site_alert.hours_threshold = timedelta(hours=int(notify_form.data['hours_threshold']))
                site_alert.save()

            elif notify_form.cleaned_data['notify'] and not site_alert:
                self.request.user.site_alerts.create(
                    site_registration=site_registration,
                    hours_threshold=timedelta(hours=int(notify_form.data['hours_threshold']))
                )

            elif not notify_form.cleaned_data['notify'] and site_alert:
                site_alert.delete()

            messages.success(request, 'The site has been updated successfully.')
            return self.form_valid(form)
        else:
            messages.error(request, 'There are still some required fields that need to be filled out!')
            return self.form_invalid(form)


class SiteRegistrationView(LoginRequiredMixin, CreateView):
    template_name = 'dataloaderinterface/site_registration.html'
    form_class = SiteRegistrationForm
    model = SiteRegistration
    object = None

    def get_success_url(self):
        return reverse_lazy('site_detail', kwargs={'sampling_feature_code': self.object.sampling_feature_code})

    @staticmethod
    def get_default_data():
        data = {
            'elevation_datum': ElevationDatum.objects.filter(pk='MSL').first(),
            'site_type': SiteType.objects.filter(pk='Stream').first()
        }
        return data

    def get_form(self, form_class=None):
        data = self.request.POST or None
        return self.get_form_class()(initial=self.get_default_data(), data=data)

    def get_context_data(self, **kwargs):
        context = super(SiteRegistrationView, self).get_context_data()
        data = self.request.POST or {}
        context['email_alert_form'] = SiteAlertForm(data)
        context['zoom_level'] = data['zoom-level'] if 'zoom-level' in data else None
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form_class()(request.POST)
        notify_form = SiteAlertForm(request.POST)

        try:
            SamplingFeature.objects.get(sampling_feature_code='asdf').delete()
        except:
            pass

        if form.is_valid() and notify_form.is_valid():
            form.instance.affiliation_id = form.cleaned_data['affiliation_id'] or request.user.affiliation_id
            form.instance.django_user = request.user
            form.instance.save()
            self.object = form.save()

            if notify_form.cleaned_data['notify']:
                self.request.user.site_alerts.create(
                    site_registration=form.instance,
                    hours_threshold=timedelta(hours=int(notify_form.data['hours_threshold']))
                )
            return super(ModelFormMixin, self).form_valid(form)
        else:
            messages.error(request, 'There are still some required fields that need to be filled out!')
            return self.form_invalid(form)

# def delete_result(result):
#     result_id = result.result_id
#     feature_action = result.feature_action
#     action = feature_action.action
#
#     result.data_logger_file_columns.all().delete()
#     result.timeseriesresult.values.all().delete()
#     result.timeseriesresult.delete()
#
#     action.action_by.all().delete()
#     result.delete()
#
#     feature_action.delete()
#     action.delete()
#     SiteSensor.objects.filter(result_id=result_id).delete()
