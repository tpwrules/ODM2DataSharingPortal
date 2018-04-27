# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random

# from django.shortcuts import render
from dataloaderinterface.models import SiteRegistration
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView, BaseDetailView
from django.views.generic.detail import DetailView
from django.shortcuts import reverse, redirect
from django.db.models import Q
from operator import __or__ as OR
from functools import reduce
from .models import LeafPack, Macroinvertebrate, LeafPackType
from .forms import LeafPackForm, LeafPackBugForm, LeafPackBugFormFactory, LeafPackBug
from django.core.management import call_command
from uuid import UUID
import re
from datetime import date, timedelta


class LeafPackDetailView(DetailView):
    template_name = 'leafpack/leafpack_detail.html'
    slug_field = 'sampling_feature_code'
    model = LeafPack

    def get_object(self, queryset=None):
        return LeafPack.objects.get(uuid=UUID(self.kwargs['uuid']))

    def get_context_data(self, **kwargs):
        context = super(LeafPackDetailView, self).get_context_data(**kwargs)
        context['leafpack'] = self.get_object()

        return context


class LeafPackCreateView(CreateView):
    form_class = LeafPackForm
    template_name = 'leafpack/leafpack_create.html'
    slug_field = 'sampling_feature_code'

    def get_context_data(self, **kwargs):

        # TODO: Probably get rid of this eventually...
        if not len(Macroinvertebrate.objects.all()):
            # If there are no macroinvertebrates in the database, run 'set_leafpackdb_defaults' command to populate
            # database with default macroinvertebrate and leaf pack types.
            call_command('set_leafpackdb_defaults')

        context = super(LeafPackCreateView, self).get_context_data(**kwargs)

        context['sampling_feature_code'] = self.kwargs[self.slug_field]

        # TODO: Remove this random leaf pack type generator stuff - for testing only...
        lpt_ids = [lp.id for lp in LeafPackType.objects.all()]
        rand_len = random.randint(1, 5)
        rand_lpts = list()
        while len(rand_lpts) < rand_len:
            lpt = random.randint(1, len(lpt_ids))
            if lpt in lpt_ids and lpt not in rand_lpts:
                rand_lpts.append(lpt)

        # TODO: Remove mock values (placement date, retrieval date, etc.) - they are for testing
        context['leafpack_form'] = LeafPackForm(initial={
            'site_registration': SiteRegistration.objects.get(sampling_feature_code=self.kwargs[self.slug_field]),
            'placement_date': date.today() - timedelta(days=7),
            'retrieval_date': date.today(),
            'placement_air_temp': 75.0,
            'placement_water_temp': 75.0,
            'retrieval_air_temp': 75.0,
            'retrieval_water_temp': 75.0,
            'leafpack_retrieval_count': 1,
            'leafpack_placement_count': 1,
            'types': LeafPackType.objects.filter(reduce(OR, [Q(id=i) for i in rand_lpts]))
        })

        context['bug_count_form_list'] = LeafPackBugFormFactory.formset_factory()

        return context

    def forms_valid(self, forms):
        is_valid = True
        for form in forms:
            if not form.is_valid():
                is_valid = False
        return is_valid

    def get_bug_count_forms(self):
        re_bug_name = re.compile(r'^(?P<bug_name>.*)-bug_count')
        form_data = list()
        for key, value in self.request.POST.iteritems():
            if 'bug_count' in key:
                form_data.append((re_bug_name.findall(key)[0], value))

        bug_forms = list()
        for data in form_data:
            bug = Macroinvertebrate.objects.get(scientific_name=data[0])
            count = data[1]

            form = LeafPackBugForm(data={'bug_count'.format(bug.scientific_name): count})
            form.instance.bug = bug
            bug_forms.append(form)

        return bug_forms

    def post(self, request, *args, **kwargs):

        leafpack_form = self.get_form()

        bug_forms = self.get_bug_count_forms()

        if self.forms_valid([leafpack_form] + bug_forms):
            leafpack_form.save()

            for bug_form in bug_forms:
                LeafPackBug.objects.create(bug=bug_form.instance.bug, leaf_pack=leafpack_form.instance,
                                           bug_count=bug_form.cleaned_data['bug_count'])

            return redirect(reverse('site_detail', kwargs={'sampling_feature_code': self.kwargs['sampling_feature_code']}))

        return self.form_invalid(leafpack_form)
