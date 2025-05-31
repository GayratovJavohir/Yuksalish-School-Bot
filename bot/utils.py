from .models import Book  # modelni to'g'ri import qiling
from asgiref.sync import sync_to_async

@sync_to_async
def get_books_for_month_and_class(month, student_class_id):
    return list(
        Book.objects.filter(
            month=month,
            uploaded_by__student_class_id=student_class_id
        ).order_by('title')
    )
