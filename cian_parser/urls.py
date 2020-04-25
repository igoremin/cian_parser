from django.urls import path
from .views import results, new_objects_parsing_form, object_info_page, proxy_file, all_results_files

urlpatterns = [
    path('new_objects_parser/', new_objects_parsing_form, name='new_objects_parsing_form_url'),
    path('object/<int:pk>/', object_info_page, name='object_info_page_url'),
    path('proxy/', proxy_file, name='proxy_file_url'),
    path('all_results_file/', all_results_files, name='all_results_file_url'),
    path('', results, name='results_url'),
]
