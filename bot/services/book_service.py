# services/book_service.py
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from django.core.cache import cache
from bot.models import Book, CustomBook

class BookService:
    @staticmethod
    @sync_to_async
    def save_book(user, title, month, file_bytes, filename):
        book = Book(title=title, month=month, uploaded_by=user)
        book.file.save(filename, ContentFile(file_bytes))
        book.save()
        return book

    @staticmethod
    @sync_to_async
    def get_books_for_month(month):
        cache_key = f"books_{month.lower()}"
        books = cache.get(cache_key)
        if not books:
            books = list(Book.objects.filter(month__iexact=month))
            cache.set(cache_key, books, timeout=60 * 60)
        return books

    @staticmethod
    @sync_to_async
    def get_book_by_id(book_id):
        return Book.objects.get(id=book_id)

    @staticmethod
    @sync_to_async
    def create_custom_book(student, month, name):
        return CustomBook.objects.create(created_by=student, month=month, name=name)

    @staticmethod
    @sync_to_async
    def get_all_books_ordered():
        return list(Book.objects.all().order_by('month', 'title'))