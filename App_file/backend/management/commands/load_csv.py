# python manage.py load_csv C:\Users\user\Downloads\output.csv 로 실행

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.models import *

class Command(BaseCommand):
    help = "CSV 파일을 읽어서 DB에 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="CSV 파일 경로")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        def clean_str(val):
            if pd.isna(val):
                return None
            s = str(val).strip()
            return s if s else ""

        def parse_runtime(val):
            if pd.isna(val) or not str(val).strip():
                return None
            try:
                h, m = map(int, str(val).split(":"))
                hours = h + m / 60
                return round(hours, 2)
            except Exception:
                return None

        df = pd.read_csv(csv_file)

        try:
            with transaction.atomic():
                for idx, row in df.iterrows():
                    # 1) 장르
                    genre_name = clean_str(row.get("Genre"))
                    genre = None
                    sub_genre = None
                    if genre_name:
                        genre, _ = Genre.objects.get_or_create(name=genre_name)
                        sub_name = clean_str(row.get("Sub_Genre"))
                        if sub_name:
                            sub_genre, _ = SubGenre.objects.get_or_create(genre=genre, name=sub_name)
                        else :
                            sub_genre, _ = SubGenre.objects.get_or_create(genre=genre, name='기타')

                    # 2) 프로그램
                    release_str = clean_str(row.get("Release"))
                    release = int(release_str) if release_str.isdigit() else None

                    program = Program.objects.create(
                        title=clean_str(row.get("Title")),
                        runtime_hour=parse_runtime(row.get("Runtime_Hours")),
                        poster=clean_str(row.get("Poster")),
                        description=clean_str(row.get("Description")),
                        program_type=clean_str(row.get("Type")),
                        release=release,
                        production=clean_str(row.get("Production")),
                        country=clean_str(row.get("Country")),
                        genre=genre,
                        sub_genre=sub_genre
                    )

                    # 3) 성과
                    hours_str = clean_str(row.get("Hours")).replace(",", "")
                    hours = int(hours_str) if hours_str.isdigit() else None

                    views_str = clean_str(row.get("Views")).replace(",", "")
                    views = int(views_str) if views_str.isdigit() else None

                    imdb_str = clean_str(row.get("IMDB"))
                    imdb = float(imdb_str) if imdb_str.replace(".", "", 1).isdigit() else None

                    rt_str = clean_str(row.get("Rotten_Tomatoes"))
                    rotten_tomatoes = int(rt_str) if rt_str.isdigit() else None

                    rank_str = clean_str(row.get("Rank"))
                    rank = int(rank_str) if rank_str.isdigit() else None

                    Performance.objects.create(
                        program=program,
                        hours=hours,
                        views=views,
                        imdb=imdb,
                        rotten_tomatoes=rotten_tomatoes,
                        rank=rank,
                        half_year=clean_str(row.get("Half_Year"))
                    )

                    # 4) 스트리밍
                    streaming_val = clean_str(row.get("Streaming"))
                    if streaming_val:
                        cleaned_val = streaming_val.strip("[]").replace("'", "").replace('(', '').replace(')', '')
                        for ott in cleaned_val.split(","):
                            ott_name = ott.strip()
                            if ott_name:
                                Streaming.objects.create(program=program, ott=ott_name)

                    # 5) 인물
                    for col, role in [("Starring", "Starring"), ("Directors", "Directors"), ("Produced_by", "Producer")]:
                        val = clean_str(row.get(col))
                        if val:
                            for name in val.split(","):
                                name_clean = name.strip()
                                if name_clean:
                                    person, _ = Person.objects.get_or_create(name=name_clean)
                                    ProgramPersonRole.objects.get_or_create(program=program, person=person, role=role)

            self.stdout.write(self.style.SUCCESS("CSV 데이터 적재 완료"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"{idx}번째 행에서 오류 발생, 전체 롤백합니다."))
            self.stderr.write(self.style.ERROR(f"에러 내용: {e}"))