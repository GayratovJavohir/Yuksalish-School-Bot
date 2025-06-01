from django.urls import path
from .views import view_task_video, view_book_file, test_task_view

urlpatterns = [
    path('task/video/<int:pk>/', view_task_video, name='view_task_video'),
    path('books/<int:pk>/file/', view_book_file, name='view_book_file'),
    path('test-celery/', test_task_view, name='test_celery'),

]
