from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=200, verbose_name='장르')

    def __str__(self):
        return self.name


class SubGenre(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name='장르')
    name = models.CharField(max_length=200, verbose_name='서브 장르')

    def __str__(self):
        return f"{self.genre.name} - {self.name}"


class Program(models.Model):
    title = models.CharField(max_length=200, verbose_name='프로그램 제목')
    runtime_hour = models.FloatField(verbose_name='상영시간 (시간)')
    poster = models.URLField(max_length=500, verbose_name='포스터 URL')
    description = models.TextField(null=True, verbose_name='프로그램 설명')
    program_type = models.CharField(max_length=100, verbose_name='프로그램 타입')  
    release = models.IntegerField(verbose_name='개봉년도')
    production = models.CharField(null=True, max_length=200, verbose_name='제작사')
    country = models.CharField(max_length=200, verbose_name='제작 국가')

    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name='장르')
    sub_genre = models.ForeignKey(
        SubGenre,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='서브 장르'
    )

    def __str__(self):
        return self.title


class Performance(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="performances")
    hours = models.BigIntegerField(verbose_name='시청 시간')
    views = models.BigIntegerField(verbose_name='조회 수')
    imdb = models.FloatField(verbose_name='IMDB 평점')
    rotten_tomatoes = models.IntegerField(null=True, blank=True, verbose_name='Rotten Tomatoes 평점')
    rank = models.IntegerField(verbose_name='순위')
    half_year = models.CharField(max_length=20, verbose_name='연도 및 반기')  

    class Meta:
        indexes = [models.Index(fields=['half_year'])]


class Streaming(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="streamings")
    ott = models.CharField(max_length=100, verbose_name='OTT 플랫폼')  

    def __str__(self):
        return f"{self.program.title} - {self.ott}"


class Person(models.Model):
    name = models.CharField(max_length=200, verbose_name='이름')

    def __str__(self):
        return self.name


class ProgramPersonRole(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='person_roles')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='program_roles')
    role = models.CharField(max_length=100, verbose_name='역할')  # ex: Starring, Director, Producer

    def __str__(self):
        return f"{self.program.title} - {self.person.name} ({self.role})"