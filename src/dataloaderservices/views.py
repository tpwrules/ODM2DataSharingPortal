from datetime import datetime

from django.db.models.expressions import F
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import exceptions

from dataloader.models import SamplingFeature, TimeSeriesResultValue, CensorCode, QualityCode, Unit, Affiliation, \
    EquipmentModel
from dataloaderinterface.models import DeviceRegistration
from dataloaderservices.auth import UUIDAuthentication
from dataloaderservices.serializers import AffiliationSerializer, PersonSerializer, OrganizationSerializer, \
    EquipmentModelSerializer


class ModelVariablesApi(APIView):
    authentication_classes = (SessionAuthentication, )

    def get(self, request, format=None):
        if 'equipment_model_id' not in request.GET:
            return Response({'error': 'Equipment Model Id not received.'})

        equipment_model_id = request.GET['equipment_model_id']
        if equipment_model_id == '':
            return Response({'error': 'Empty Equipment Model Id received.'})

        equipment_model = EquipmentModel.objects.filter(pk=equipment_model_id).first()
        if not equipment_model:
            return Response({'error': 'Equipment Model not found.'})

        return Response(EquipmentModelSerializer(equipment_model).data)


class AffiliationApi(APIView):
    authentication_classes = (SessionAuthentication, )

    def get(self, request, format=None):
        if 'affiliation_id' not in request.GET:
            return Response({'error': 'Affiliation Id not received.'})

        affiliation_id = request.GET['affiliation_id']
        if affiliation_id == '':
            return Response({'error': 'Empty Affiliation Id received.'})

        affiliation = Affiliation.objects.filter(pk=affiliation_id).first()
        if not affiliation:
            return Response({'error': 'Affiliation not found.'})

        return Response(AffiliationSerializer(affiliation).data)

    def post(self, request, format=None):
        person_serializer = PersonSerializer(data=request.data)
        organization_serializer = OrganizationSerializer(data=request.data)
        affiliation_serializer = AffiliationSerializer(data=request.data)

        if person_serializer.is_valid() and organization_serializer.is_valid() and affiliation_serializer.is_valid():
            person_serializer.save()
            organization_serializer.save()
            affiliation_serializer.save(
                person=person_serializer.instance,
                organization=organization_serializer.instance
            )
            return Response(affiliation_serializer.data, status=status.HTTP_201_CREATED)

        error_data = dict(person_serializer.errors, **organization_serializer.errors)
        error_data.update(affiliation_serializer.errors)

        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class TimeSeriesValuesApi(APIView):
    authentication_classes = (UUIDAuthentication, )

    def post(self, request, format=None):
        #  make sure that the data is in the request (sampling_feature, timestamp(?), ...) if not return error response
        # if 'sampling_feature' not in request.data or 'timestamp' not in request.data:
        if not all(key in request.data for key in ('timestamp', )):
            raise exceptions.ParseError("Keys sampling_feature or timestamp values not present in the request.")

        # parse the received timestamp
        values_timestamp = try_parsing_date(request.data['timestamp'])

        # get odm2 sampling feature if it matches sampling feature uuid sent
        sampling_feature_uuid = request.data['sampling_feature']
        sampling_feature = SamplingFeature.objects.filter(sampling_feature_uuid__exact=sampling_feature_uuid).first()
        if not sampling_feature:
            raise exceptions.ParseError('Sampling Feature UUID does not match any existing Sampling Feature')

        # get all feature actions related to the sampling feature, along with the results, results variables, and actions.
        feature_actions = sampling_feature.feature_actions.prefetch_related('results__variable', 'action').all()
        for feature_action in feature_actions:
            result = feature_action.results.all().first()

            # don't create a new TimeSeriesValue for results that are not included in the request
            if str(result.result_uuid) not in request.data:
                continue

            result_value = TimeSeriesResultValue(
                result_id=result.result_id,
                value_datetime_utc_offset=feature_action.action.begin_datetime_utc_offset,
                value_datetime=values_timestamp,
                censor_code_id='Not censored',
                quality_code_id='None',
                time_aggregation_interval=1,
                time_aggregation_interval_unit=Unit.objects.get(unit_name='hour minute'),
                data_value=request.data[str(result.result_uuid)]
            )

            try:
                result_value.save()
            except Exception as e:
                raise exceptions.ParseError("{variable_code} value not saved {exception_message}".format(
                    variable_code=result.variable.variable_code, exception_message=e
                ))

            result.value_count = F('value_count') + 1
            result.result_datetime = values_timestamp
            result.result_datetime_utc_offset = feature_action.action.begin_datetime_utc_offset
            result.save(update_fields=['result_datetime', 'value_count', 'result_datetime_utc_offset'])

        return Response({}, status.HTTP_201_CREATED)


def try_parsing_date(text):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    raise exceptions.ParseError('no valid date format found')
