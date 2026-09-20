from django.urls import path

from . import views

app_name = 'zoo'

urlpatterns = [
    path('', views.asg_list, name='asg_list'),
    path('asg/<int:asg_id>/calendar/', views.calendar_tab, name='calendar_tab'),
    path('asg/<int:asg_id>/calendar/<int:year>/<int:month>/', views.calendar_tab, name='calendar_tab'),
    path('asg/<int:asg_id>/calendar/<int:year>/<int:month>/print/', views.calendar_print, name='calendar_print'),
    path('asg/<int:asg_id>/calendar/<int:year>/<int:month>/copy/', views.calendar_copy, name='calendar_copy'),
    path('asg/<int:asg_id>/calendar/<int:year>/<int:month>/paste/', views.calendar_paste, name='calendar_paste'),
    path('asg/<int:asg_id>/list/', views.list_management_tab, name='list_management_tab'),
    path('asg/<int:asg_id>/list/print/', views.list_management_print, name='list_management_print'),
    path('asg/<int:asg_id>/report/', views.reporting_view, name='reporting_view'),

    path('training/', views.training_start, name='training_start'),
    path('training/ajax_animals_for_string/', views.training_ajax_animals_for_string, name='training_ajax_animals_for_string'),
    path('divisions/', views.set_divisions, name='set_divisions'),
    path('training/manage/', views.manage_training, name='manage_training'),
    path('training/animal/<int:animal_id>/', views.training_entry, name='training_entry'),
    path('training/animal/<int:animal_id>/history/', views.training_history, name='training_history'),

    path('supervisor/items/remove_from_asgs/', views.item_remove_from_asgs, name='item_remove_from_asgs'),
    path('supervisor/items/ajax_asgs_for_item/', views.item_ajax_asgs_for_item, name='item_ajax_asgs_for_item'),
]
