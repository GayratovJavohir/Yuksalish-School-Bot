from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
import os

from .models import StudentTask, Book


def serve_protected_file(file_field, request, content_type=None):
    """Helper function to serve protected files"""
    if not file_field:
        return HttpResponse("File not found", status=404)

    if not os.path.exists(file_field.path):
        return HttpResponse("File not found on server", status=404)

    response = FileResponse(
        file_field.open('rb'),
        content_type=content_type or 'application/octet-stream'
    )
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_field.name)}"'
    return response


@login_required
def view_task_video(request, pk):
    task = get_object_or_404(StudentTask, pk=pk)

    # Permission check
    if not (request.user.is_staff or request.user == task.student):
        return HttpResponseForbidden("You don't have permission to view this video")

    return serve_protected_file(
        task.video_file,
        request,
        content_type='video/mp4'
    )


@login_required
def view_book_file(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Permission check - allow coordinators and the uploader
    if not (request.user.is_staff or request.user == book.uploaded_by):
        return HttpResponseForbidden("You don't have permission to view this book")

    # Determine content type based on file extension
    ext = os.path.splitext(book.file.name)[1].lower()
    content_type = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
    }.get(ext, 'application/octet-stream')

    return serve_protected_file(
        book.file,
        request,
        content_type=content_type
    )


from django.http import JsonResponse
from .tasks import send_daily_reminders
def test_task_view(request):
    send_daily_reminders.delay()
    return JsonResponse({"message": "Celery task yuborildi!"})
