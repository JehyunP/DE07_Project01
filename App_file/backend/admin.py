from django.contrib import admin
from .models import *

# 인라인으로 SubGenre를 Genre 안에서 관리할 수 있도록
class SubGenreInline(admin.TabularInline):
    model = SubGenre
    extra = 1


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = [SubGenreInline]


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


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'half_year', 'hours', 'views', 'imdb', 'rotten_tomatoes', 'rank')
    list_filter = ('half_year',)
    search_fields = ('program__title',)


@admin.register(Streaming)
class StreamingAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'ott')
    list_filter = ('ott',)
    search_fields = ('program__title',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ProgramPersonRole)
class ProgramPersonRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'person', 'role')
    list_filter = ('role',)
    search_fields = ('program__title', 'person__name')