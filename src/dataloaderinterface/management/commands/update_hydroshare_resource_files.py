from django.core.management.base import BaseCommand, CommandError
from dataloaderinterface.models import HydroShareResource
from dataloaderinterface.views import upload_hydroshare_resource_files
from hydroshare_util.resource import Resource
from hydroshare_util.utility import AuthUtil
from django.utils.termcolors import colorize

class Command(BaseCommand):
    def handle(self, *args, **options):
        resources = HydroShareResource.objects.all()
        upload_success_count = 0
        upload_fail_count = 0
        self.stdout.write(colorize('\nStarting Job: ', fg='blue') + 'Uploading site data to hydroshare')
        for resource in resources:
            site = resource.site_registration

            self.stdout.write(colorize('Uploading resource files for: ', fg='blue') + site.sampling_feature_code)

            try:
                auth = AuthUtil.authorize(token=resource.hs_account.token.to_dict())
                hs_resource = Resource(client=auth.get_client(), resource_id=resource.ext_id)
                # upload_hydroshare_resource_files(site, hs_resource)
                upload_success_count += 1

                self.stdout.write(colorize('\tSuccessfully uploaded file(s) for {0}'.format(site.sampling_feature_code), fg='blue'))

            except Exception as e:
                upload_fail_count += 1
                self.stderr.write(colorize('ERROR: file upload failed, reason given:\n\t{0}'.format(e.message), fg='red'))

        self.stdout.write(colorize('\nJob finished uploading resource files to hydroshare.', fg='blue'))
        self.stdout.write(colorize('\tResource upload success count: ', fg='blue') + str(upload_success_count))
        self.stdout.write(colorize('\t   Resource upload fail count: ', fg='blue') + str(upload_fail_count))
        self.stdout.write(colorize('\t                    Attempted: ', fg='blue') + str(len(resources)) + '\n')

