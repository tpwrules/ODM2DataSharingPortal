from django import forms
#from .models import LeafPack, LeafPackType, Macroinvertebrate, LeafPackBug, LeafPackSensitivityGroup
from dataloaderinterface.models import SiteRegistration
from django.core.exceptions import ObjectDoesNotExist
from leafpack.models import LeafPackType
from .models import variable_choice_options

place_holder_choices = (
        (1, 'Choice #1'), 
        (2, 'Choice #2'),
        (3, 'Choice #3')
    )
class MDLCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = 'mdl-checkbox-select-multiple.html'

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        context['choices'] = [choice[1][0] for choice in context['widget']['optgroups']]
        context['name'] = name
        return self._render(self.template_name, context, renderer)

class StreamWatchForm(forms.Form):
    
    ACTIVITY_TYPE_CHOICES = (('chemical', 'Chemical Action Team'), ('biological', 'Biological Action Team'), ('baterial', 'Baterial Action Team'))

    def __init__(self, *args, **kwargs):
        super(StreamWatchForm, self).__init__(*args, **kwargs)
        #self.fields['types'].initial = self.ACTIVITY_TYPE_CHOICES_LIST
    
    investigator1 = forms.CharField(
        required=False,
        label='Investigator #1'
    )       
    investigator2 = forms.CharField(
        required=False,
        label='Investigator #2'
    )   
    collect_date = forms.DateField(
        required=False,
        label='Date'
    )
    collect_time = forms.TimeField(
        required=False,
        label='Time'
    )
    # mutiple choices
    activity_types = forms.MultipleChoiceField(
        widget=MDLCheckboxSelectMultiple,
        label='Activity type(s):',
        required=True,
        choices = ACTIVITY_TYPE_CHOICES)    

    
class StreamWatchForm2(forms.Form):
    weather_condition_choices = (
        (1, 'Clear'),
        (2, 'Partly cloudy'),
        (3, 'Overcast')
    )
    water_color_choices = ((1,'Clear'),
        (2,'Green'),
        (3,'Blue-green'),
        (4,'Brown'),
        (5,'Yellow'),
        (6,'Gray'),
        (7,'Other'))

    water_odor_choices = (
        (1,'Normal'),
        (2,'Anaerobic'),
        (3,'Sulfuric'),
        (4,'Sewage'),
        (5,'Petroleum'),
        (6,'Other'))

    abundance_choices = variable_choice_options('wildlife')
    # types = forms.ModelMultipleChoiceField(
    #     widget=MDLCheckboxSelectMultiple,
    #     label='Activity type(s):',
    #     required=True,
    #     queryset=LeafPackType.objects.filter(created_by=None),
    # )

    #Wildlife Observations
    # wildlife_obs = forms.ModelMultipleChoiceField(
    #     widget=MDLCheckboxSelectMultiple,
    #     required=True,
    #     label='Wildlife Observations:',
    #     queryset= abundance_choices,
    # )
    
    # single choice
    weather_cond = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        label='Current Weather Conditions:',
        choices= weather_condition_choices,
        initial='1'
    )
    time_since_last_precip = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        label='Time Since Last Rain or Snowmelt:',
        choices= place_holder_choices,
        initial='1'
    )
    
    water_color = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        label='Water Color:',
        choices= variable_choice_options('waterColor'),
        initial='1'
    )
    water_odor = forms.MultipleChoiceField(
        widget=MDLCheckboxSelectMultiple,
        required=True,
        label='Water Odor:',
        choices= water_odor_choices,
    )
        
    # floating number input
    air_temp = forms.FloatField(
        label='Air Temperature',
        required=False,
    )
    
    turbidity = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        label='Turbidity:',
        choices= place_holder_choices,
        initial='1'
    )
    
    water_movement = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        label='Turbidity:',
        choices= place_holder_choices,
        initial='1'
    )

    
    
class StreamWatchForm3(forms.Form):
    aquatic_vegetation = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        label='Aquatic Vegetation:',
        choices= place_holder_choices,
        initial='1'
    )
    surface_coating = forms.MultipleChoiceField(
        widget=MDLCheckboxSelectMultiple,
        required=True,
        label='Surface Coating:',
        choices= place_holder_choices,
    )