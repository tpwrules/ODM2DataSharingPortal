from django.conf.urls import url

from streamwatch import views

urlpatterns = [
    url(r'(?P<pk>.*?)/addsensor/$', views.StreamWatchCreateMeasurementView.as_view(), name='addsensor'),
    url(r'create/$', views.CreateView.as_view(), name='create'),
    url(r'delete/$', views.DeleteView.as_view(), name='delete'),
    url(r'(?P<pk>.*?)/update/$', views.UpdateView.as_view(), name='update'),
    url(r'(?P<pk>.*?)/csv/$', views.download_StreamWatch_csv, name='csv_download'),
    url(r'(?P<pk>.*?)/$', views.StreamWatchDetailView.as_view(), name='view'),
]    
