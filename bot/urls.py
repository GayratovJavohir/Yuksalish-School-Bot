from django.urls import path
from .views import view_task_video, view_book_file

urlpatterns = [
    path('task/video/<int:pk>/', view_task_video, name='view_task_video'),
    path('books/<int:pk>/file/', view_book_file, name='view_book_file'),
]
