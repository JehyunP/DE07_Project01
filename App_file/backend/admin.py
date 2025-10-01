from django.contrib import admin
from .models import *



# Program 관리 화면에서 Streaming, Performance, ProgramPersonRole을 인라인으로 관리
class StreamingInline(admin.TabularInline):
    model = Streaming
    extra = 1


class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 1


class ProgramPersonRoleInline(admin.TabularInline):
    model = ProgramPersonRole
    extra = 1


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'program_type', 'release', 'production', 'country', 'genre', 'sub_genre')
    list_filter = ('program_type', 'release', 'genre')
    search_fields = ('title', 'production', 'country')

    inlines = [StreamingInline, PerformanceInline, ProgramPersonRoleInline]
