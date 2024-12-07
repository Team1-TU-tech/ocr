import boto3
from requests_html import HTML
from bs4 import BeautifulSoup
import certifi
from ocr.get_img import ocr
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os, re

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="ap-northeast-2"
    )

objects = s3.list_objects(Bucket = 't1-tu-data', Prefix='yes24/')['Contents']

#mongodb
mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://summerham22:{mongopassword}@cluster0.5vlv3.mongodb.net/tut?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(url, tlsCAFile=certifi.where())
db = client.tut

def s3_to_mongodb(start_id):
    while True:
        for i in objects:
            filename = i["Key"]
            if filename.endswith('.html'):
                title = filename.split('/')[1].split('.')[0]
                ticket_url = f'http://ticket.yes24.com/Perf/{title}'
                response = s3.get_object(Bucket='t1-tu-data', Key=f'yes24/{title}.html')
                
                file_content = response['Body'].read().decode('utf-8')
                soup = BeautifulSoup(file_content, "html.parser")
            
                # 카테고리
                category_element = soup.select_one('.rn-location a')
                category = category_element.text.strip() if category_element else None

                # 단독판매 여부
                exclusive_sales_element = soup.select_one('.rn-label')
                exclusive_sales = exclusive_sales_element.text.strip() if exclusive_sales_element else None

                # 공연 제목
                title_element = soup.select_one('.rn-big-title')
                original_title = title_element.text.strip() if title_element else None
                # title_element가 None이 아닐 경우에만 텍스트를 처리
                if title_element:
                    title = re.sub(r'[^가-힣A-Za-z0-9]', '',title_element.text.strip())
                else:
                    title = None

                # 공연일자
                show_time_element = soup.select_one('.rn-product-area3 dd')
                show_time = show_time_element.text.strip() if show_time_element and show_time_element.text.strip() not in ("", "-") else None

                # 시작일자와 종료일자
                date_element = soup.select_one('.ps-date')
                if date_element:
                    date_text = date_element.text.strip()
                    start_date, end_date = map(str.strip, date_text.split('~'))  # 양쪽 공백 제거
                else:
                    start_date = None
                    end_date = None

                #DuplicateKey 중복데이터 구별을 위한 컬럼
                duplicate_key = f"{title}{start_date}"

                # 공연 상세 정보
                performance_details = soup.select('.rn08-tbl td')
                
                running_time = performance_details[5].text.strip() if len(performance_details) > 5 and performance_details[5].text.strip() not in ("", "-") else None
                age_rating = performance_details[4].text.strip() if len(performance_details) > 4 and performance_details[4].text.strip() not in ("", "-") else None
                performance_place = performance_details[6].text.strip() if len(performance_details) > 6 else None

                # 가격 정보
                price_elements = soup.select('.rn-product-price1 li')
                # 'price' 리스트 안에 여러 석 정보 추가
                price_info = []
                
                if price_elements:
                    for seat in price_elements:
                        # 석 이름과 가격 부분을 추출
                        seat_name = seat.contents[0].strip()  # 'R석' 또는 'S석'
                        price = seat.find('span', class_='rn-red').text.strip() + "원"

                        # 정보를 리스트 형식으로 추가
                        price_info.append({"seat": seat_name, "price": price})

                else: price_info = None

                # 포스터 이미지 URL
                poster_img_element = soup.select_one('.rn-product-imgbox img')
                poster_img = poster_img_element['src'] if poster_img_element else None

                # 혜택 및 할인 정보
                benefits_element = soup.select_one('.rn-product-dc')
                benefits = benefits_element.text.strip() if benefits_element else None

                # 출연진 정보
                performer_elements = soup.select('.rn-product-peole')

                performer_info = []
                if performer_elements:
                    performer_names = [performer.text.strip() for performer in performer_elements]
                    performer_links = [performer.get('href') for performer in performer_elements]

                    # 두 개의 리스트를 묶어서 딕셔너리 형식으로 저장
                    for name, link in zip(performer_names, performer_links):
                        performer_info.append({"artist_name": name, "artist_url": link})
                else:
                    performer_info = None

                # 호스팅 서비스 사업자 정보
                hosting_provider_element = soup.select_one('.footxt p')
                hosting_provider = hosting_provider_element.text.strip() if hosting_provider_element else None

                # 주최자 정보
                organizer_info_element = soup.select_one('#divPerfOrganization')
                organizer_info = organizer_info_element.text.strip() if organizer_info_element else None
            
                # 지역 정보
                area_mapping = {
                                '서울': '서울',
                                '경기': '수도권',
                                '인천': '수도권',
                                '부산': '경상',
                                '대구': '경상',
                                '울산': '경상',
                                '경남': '경상',
                                '경북': '경상',
                                '전북': '전라',
                                '전주': '전라',
                                '광주': '전라',
                                '전남': '전라',
                                '충북': '충청',
                                '대전': '충청',
                                '강원': '강원',
                                '제주': '제주'
                                }
                area_element = soup.select_one('#TheaterAddress')
                area = area_element.get_text().split(' ')[0][:2] if area_element else None
                area = area_mapping.get(area, '기타')

                # 상세정보 이미지
                div_content = soup.find('div', attrs={"id": ["divPerfContent", "divPerfNotice"]})
                
                # 모든 OCR 결과를 저장할 리스트
                all_descriptions = []

                if div_content:
                    # 모든 이미지 태그 찾기
                    img_tags = div_content.find_all('img', class_='txc-image')

                    if img_tags:
                        for idx, img_tag in enumerate(img_tags, start=1):
                            img_url = img_tag.get('src')  # 이미지 URL 가져오기
                            print(f"[{idx}] 이미지 URL: {img_url}")

                            if img_url:
                                try:
                                    description = ocr(image_url=img_url)
                                    print(f"[{idx}] OCR 결과:\n{description}")
                                    all_descriptions.append(description)  # 결과 누적
                                except Exception as e:
                                    print(f"[{idx}] OCR 실패: {e}")
                                    all_descriptions.append("상세설명이 없습니다.")
                            else:
                                print(f"[{idx}] 이미지 URL을 찾을 수 없습니다.")
                                all_descriptions.append("상세설명이 없습니다.")
                    else:
                        print("이미지 태그를 찾을 수 없습니다.")
                        all_descriptions.append("상세설명이 없습니다.")
                else:
                    print("divPerfContent를 찾을 수 없습니다.")
                    all_descriptions.append("상세설명이 없습니다.")

                # 모든 OCR 결과를 하나의 문자열로 합치기
                final_description = "\n".join(all_descriptions)

                # 결과 출력
            
                print(f"title: {original_title}")
                print(f"duplicatekey: {duplicate_key}")
                print(f"category: {category}")
                print(f"location: {performance_place}")
                print(f"price: {price_info}")
                print(f"start_date: {start_date}")
                print(f"end_date: {end_date}")
                print(f"running_time: {running_time}")
                print(f"rating: {age_rating}")
                print(f"description: {final_description}")
                print(f"poster_url: {poster_img}")
                print(f"artist: {performer_info}")
                print(f"region: {area}")

                # 중복된 데이터가 존재하는지 체크
                existing_data = db.ticket.find_one({"duplicatekey": duplicate_key})

                if existing_data is None:
                    # 중복된 데이터가 없으면 새로운 데이터 삽입
                    try:
                        #db.Shows.create_index([('title', 1),('start_date', 1)],unique=True)
                        print(f"Inserting new data: {duplicate_key}")

                        db.ticket.insert_one({
                            "title": original_title,
                            "duplicatekey": duplicate_key,
                            "category": category,
                            "location": performance_place,
                            "price": price_info,
                            "start_date": start_date,
                            "end_date": end_date,
                            "running_time": running_time,
                            "casting": None,
                            "rating": age_rating,
                            "description": final_description,
                            "poster_url": poster_img,
                            "region": area,
                            "open_date": None,
                            "pre_open_date": None,
                            "artist": performer_info,
                            "hosts": [{"site_id": 2, "ticket_url":ticket_url}]
                        })
                        
                    except DuplicateKeyError:
                        print(f"Duplicate key error: {duplicate_key}")
                else:
                        # 이미 데이터가 존재하면 hosts 필드만 업데이트
                        print(f"Data already exists for {duplicate_key}. Updating hosts.")
                        previous_data = db.ticket.find_one({"duplicatekey":duplicate_key})
                        previous_data = previous_data["hosts"]

                        if len(previous_data) < 2:
                            previous_data.append({"site_id":2, "ticket_url":ticket_url})
                            db.ticket.update_one({"duplicatekey":duplicate_key},{"$set":{"hosts":previous_data}})
  
        return title
            
if __name__ == '__main__':
    s3_to_mongodb()
