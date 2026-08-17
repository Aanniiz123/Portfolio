from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import VideoProject, ContactMessage


@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "client", "featured", "order", "created_at", "thumbnail_preview")
    list_filter = ("category", "featured")
    search_fields = ("title", "client", "description")
    list_editable = ("featured", "order")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Details", {
            "fields": ("title", "slug", "category", "client", "description"),
        }),
        ("Media", {
            "fields": ("video_url", "thumbnail", "thumbnail_preview", "cover_color"),
        }),
        ("Display", {
            "fields": ("featured", "order"),
        }),
    )
    readonly_fields = ("thumbnail_preview",)

    def thumbnail_preview(self, obj):
        if obj is None:
            return mark_safe(
                '<span style="color:#888;">Save the project first, then upload a thumbnail here.</span>'
            )
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height:120px; border-radius:6px;" />',
                obj.thumbnail.url,
            )
        return mark_safe(
            '<span style="color:#888;">No thumbnail uploaded</span>'
        )
    thumbnail_preview.short_description = "Thumbnail preview"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "received_at")
    search_fields = ("name", "email", "subject")
    readonly_fields = ("name", "email", "subject", "message", "received_at")