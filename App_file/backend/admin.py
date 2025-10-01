from django.contrib import admin
from .models import *


# ---------------------------
# 인라인 설정
# ---------------------------
class StreamingInline(admin.TabularInline):
    model = Streaming
    extra = 1


class PerformanceInline(admin.TabularInline):
    model = Performance
    fields = ('half_year', 'views', 'hours', 'imdb', 'rotten_tomatoes', 'rank')
    extra = 1


class ProgramPersonRoleInline(admin.TabularInline):
    model = ProgramPersonRole
    fields = ('person', 'role')
    extra = 1
    autocomplete_fields = ('person',)   # 인물 검색창으로 선택 가능


# ---------------------------
# Genre / SubGenre / Person
# ---------------------------
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)  # 자동완성용 검색 필드


@admin.register(SubGenre)
class SubGenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'genre')
    search_fields = ('name',)  # 자동완성용 검색 필드
    list_filter = ('genre',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)  # 자동완성용 검색 필드


# ---------------------------
# Program
# ---------------------------
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title',)   # 목록 화면에서는 프로그램 제목만
    search_fields = ('title',)
    list_filter = ()

    autocomplete_fields = ('genre', 'sub_genre')  # 드롭다운 대신 검색창

    inlines = [StreamingInline, PerformanceInline, ProgramPersonRoleInline]
