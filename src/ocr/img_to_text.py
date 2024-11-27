import boto3
from requests_html import HTML
from bs4 import BeautifulSoup
import certifi
from ocr.get_img import ocr
from pymongo import MongoClient
import os

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv(AWS_ACCESS_KEY_ID),
    aws_secret_access_key=os.getenv(AWS_SECRET_ACCESS_KEY),
    region_name="ap-northeast-2"
    )

objects = s3.list_objects(Bucket = 't1-tu-data', Prefix='yes24/')['Contents']

#mongodb
#url = "mongodb+srv://summerham22:${MONGOPASS}@cluster0.c1zjv.mongodb.net/"
#client = MongoClient(url, tlsCAFile=certifi.where())
#db = client.TicketMoa

def s3_to_mongodb():
    for i in objects:
        filename = i["Key"]
    
        if filename.endswith('.html'):
            title = filename.split('.')[0]
            #ticket_url = 'http://ticket.yes24.com/Perf/51670'
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
            title = title_element.text.strip() if title_element else None

            # 공연일자
            show_time_element = soup.select_one('.rn-product-area3 dd')
            show_time = show_time_element.text.strip() if show_time_element else None

            # 시작일자와 종료일자
            date_element = soup.select_one('.ps-date')
            if date_element:
                date_text = date_element.text.strip()
                start_date, end_date = map(str.strip, date_text.split('~'))  # 양쪽 공백 제거
            else:
                start_date = None
                end_date = None

            # 공연 상세 정보
            performance_details = soup.select('.rn08-tbl td')
            running_time = performance_details[5].text.strip() if len(performance_details) > 5 else None
            age_rating = performance_details[4].text.strip() if len(performance_details) > 4 else None
            performance_place = performance_details[6].text.strip() if len(performance_details) > 6 else None

            # 가격 정보
            price_elements = soup.select('#divPrice .rn-product-price1')
            price = price_elements[0].text.strip() if price_elements else None

            # 포스터 이미지 URL
            poster_img_element = soup.select_one('.rn-product-imgbox img')
            poster_img = poster_img_element['src'] if poster_img_element else None

            # 혜택 및 할인 정보
            benefits_element = soup.select_one('.rn-product-dc')
            benefits = benefits_element.text.strip() if benefits_element else None

            # 출연진 정보
            performer_elements = soup.select('.rn-product-peole')
            performer_names = [performer.text.strip() for performer in performer_elements]
            performer_links = [performer.get('href') for performer in performer_elements]

            # 출연진 정보가 없을 경우 빈 값 처리
            if not performer_names:
                performer_names.append(None)
                performer_links.append(None)

            # 호스팅 서비스 사업자 정보
            hosting_provider_element = soup.select_one('.footxt p')
            hosting_provider = hosting_provider_element.text.strip() if hosting_provider_element else None

            # 주최자 정보
            organizer_info_element = soup.select_one('#divPerfOrganization')
            organizer_info = organizer_info_element.text.strip() if organizer_info_element else None
            
            # 상세정보 이미지
            div_content = soup.find('div', id="divPerfContent")
            
            if div_content:
                # 모든 이미지 태그 찾기
                img_tags = div_content.find_all('img', class_='txc-image')
                
                # 모든 OCR 결과를 저장할 리스트
                all_descriptions = []

                if img_tags:
                    for idx, img_tag in enumerate(img_tags, start=1):
                        img_url = img_tag.get('src')  # 이미지 URL 가져오기
                        print(f"[{idx}] 이미지 URL: {img_url}")

                        if img_url:
                            try:
                                description = ocr(img_url)
                                print(f"[{idx}] OCR 결과:\n{description}")
                                all_descriptions.append(description)  # 결과 누적
                            except Exception as e:
                                print(f"[{idx}] OCR 실패: {e}")
                                all_descriptions.append(f"OCR 실패: {e}")
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
            
            print(f"title: {title}")
            print(f"category: {category}")
            print(f"location: {performance_place}")
            print(f"price: {price}")
            print(f"start_date: {start_date}")
            print(f"end_date: {end_date}")
            print(f"show_time: {show_time}")
            print(f"running_time: {running_time}")
            print(f"rating: {age_rating}")
            print(f"description: {final_description}")
            print(f"poster_url: {poster_img}")

            db.Shows.insert_one({
                "title": title,
                "category": category,
                "location": performance_place,
                "price": price,
                "start_date": start_date,
                "end_date": end_date,
                "show_time": show_time,
                "running_time": running_time,
                "rating": age_rating,
                "description": final_description,
                "poster_url": poster_img,
                "hosts": [{"site_id": 2, "url":ticket_url}]
            })
    

if __name__ == '__main__':
    s3_to_mongodb()
