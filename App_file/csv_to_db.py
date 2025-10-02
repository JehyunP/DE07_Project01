import traceback
import pandas as pd
import os
import django

# 외부스크립트에서 접근하기 위한 Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 모델 클래스 임포트
from backend.models import Genre, SubGenre, Program, Performance, Streaming, Person, ProgramPersonRole


# 기존 저장된 데이터 삭제가 필요할 때
# def clear_tables():
#     Genre.objects.all().delete()
#     SubGenre.objects.all().delete()
#     Program.objects.all().delete()
#     Performance.objects.all().delete()
#     Streaming.objects.all().delete()
#     Person.objects.all().delete()
#     ProgramPersonRole.objects.all().delete()


# 런타임 문자열 -> float 변환 ex) 1:30 -> 1.5
def convert_runtime(runtime_str):
    if not runtime_str:
        return 0.0
    # try:
    #     return float(runtime_str)
    # except ValueError:
    #     pass
    try:
        if ':' in str(runtime_str):
            parts = str(runtime_str).split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            return round(hours + (minutes / 60), 2)
        else:
            return float(runtime_str)
    except:
        return 0.0

# 콤마(,)가 포함된 문자열 숫자 -> int 변환 ex) 10,000,000 -> 10000000
def clean_int(x):
    if x is None:
        return 0
    try:
        return int(str(x).replace(",", ""))
    except ValueError:
        return 0
def clean_float(x):
    if x is None:
        return 0.0
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return 0.0


# csv 파일을 pandas로 읽어서 Django 모델에 저장
def load_csv_to_db(csv_file_path):
    print("CSV 파일 읽기 시작")
    df = pd.read_csv(csv_file_path, encoding='utf-8')
    print(f"\nCSV 칼럼 구성: {df.columns.tolist()}\n")
    
    # pandas 결측치 NaN -> None 변환
    df = df.where(pd.notna(df), None)
    print(f"총 {len(df)}개의 데이터 처리 시작\n")
    
    success_count = 0
    fail_count = 0
    for idx, row in df.iterrows():
        try:
            print(f"\n[{idx+1}/{len(df)}] 처리 중: {row.get('Title', 'Unknown')}")
            
            # Genre 가져오기
            print(f" 1. Genre 처리: {row.get('Genre', 'N/A')}")
            genre_name = row['Genre'].strip() if row['Genre'] else 'Unknown'
            genre, created = Genre.objects.get_or_create(name=genre_name)
            if created: print(f"새 Genre 생성: {genre_name}")
                
            # SubGenre 가져오기
            sub_genre = None    # 서브장르 null값 허용
            if row.get('Sub_Genre'):
                print(f" 2. SubGenre 처리: {row['Sub_Genre']}")
                sub_genre_name = row['Sub_Genre'].strip()
                sub_genre, created = SubGenre.objects.get_or_create(genre=genre, name=sub_genre_name)
                if created: print(f"새 SubGenre 생성: {sub_genre_name}")
                    
            # Program 생성
            print(f" 3. Program 처리")
            program_data = {
                'runtime_hour': convert_runtime(row.get('Runtime_Hours')),
                'poster': row['Poster'].strip() if row.get('Poster') else '',
                'description': row['Description'].strip() if row.get('Description') else '',
                'program_type': row['Type'].strip() if row.get('Type') else '',
                'release': clean_int(row.get('Release')),
                'production': row['Production'].strip() if row.get('Production') else '',
                'country': row['Country'].strip() if row.get('Country') else '',
                'genre': genre,
                'sub_genre': sub_genre,
            }
            program, created = Program.objects.get_or_create(
                title=row['Title'].strip() if row.get('Title') else '',
                defaults=program_data
            )
            if created: print(f"새 Program 생성")
            
            # Performance 가져오기
            print(f" 4. Performance 처리")
            Performance.objects.create(
                program=program,
                hours=clean_int(row.get('Hours')),
                views=clean_int(row.get('Views')),
                imdb=clean_float(row.get('IMDB')),
                rotten_tomatoes=clean_float(row.get('Rotten_Tomatoes')),
                rank=clean_int(row.get('Rank')),
                half_year=row['Half_Year'].strip(),
            )
            
            # Streaming 생성
            if row.get('Streaming'):
                print(f"5. Streaming 처리: {row['Streaming']}")
                streaming_platforms = str(row['Streaming']).split(',')
                for ott in streaming_platforms:
                    ott = ott.strip()
                    if ott:
                        Streaming.objects.get_or_create(program=program, ott=ott)
                        
            # Starring(주연배우) 추가
            if row.get('Starring'):
                print(f" 6. Starring 처리")
                starring_list = str(row['Starring']).split(',')
                for name in starring_list:
                    name = name.strip()
                    if name:
                        person, _ = Person.objects.get_or_create(name=name)
                        ProgramPersonRole.objects.get_or_create(
                            program=program,
                            person=person,
                            role='Starring'
                        )
                        
            # Directors(감독) 추가
            if row.get('Directors'):
                print(f" 7. Directors 처리")
                directors_list = str(row['Directors']).split(',')
                for name in directors_list:
                    name = name.strip()
                    if name:
                        person, _ = Person.objects.get_or_create(name=name)
                        ProgramPersonRole.objects.get_or_create(
                            program=program,
                            person=person,
                            role='Director'
                        )
                        
            # Producers(제작자) 추가
            if row.get('Produced_by'):
                print(f" 8. Producers 처리")
                producers_list = str(row['Produced_by']).split(',')
                for name in producers_list:
                    name = name.strip()
                    if name:
                        person, _ = Person.objects.get_or_create(name=name)
                        ProgramPersonRole.objects.get_or_create(
                            program=program,
                            person=person,
                            role='Producer'
                        )
                        
            success_count += 1
        
        except Exception as e:
            fail_count += 1
            print(f"\n[{idx+1}/{len(df)}] {row.get('Title', 'Unknown')} 저장 실패")
            print(f"에러 타입: {type(e).__name__}")
            print(f"에러 메시지: {str(e)}")
            print(f"상세 정보:")
            print(traceback.format_exc())
            print("-" * 50)
            if fail_count == 1:
                print("\n에러 발생")
                break

if __name__ == '__main__':
    # clear_tables()
    
    csv_path = 'flixpatrol_data.csv'
    load_csv_to_db(csv_path)
    print("\n저장 완료")


# python manage.py shell
# python csv_to_db.py