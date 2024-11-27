import requests
from PIL import Image
from io import BytesIO
import numpy as np
import easyocr
from multiprocessing import Pool

reader = easyocr.Reader(['ko', 'en'])

# 이미지 다운로드
def download_image(url):
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

# 이미지 크기 조정
def resize_image(image, max_width=1000):
    width, height = image.size
    if width > max_width:
        new_height = int(max_width * height / width)
        return image.resize((max_width, new_height))
    return image

# 이미지 분할
def split_image(image, height_limit=1000):
    width, height = image.size
    parts = []
    for i in range(0, height, height_limit):
        box = (0, i, width, min(i + height_limit, height))
        parts.append(image.crop(box))
    return parts

# Numpy 변환
def pil_to_numpy(image):
    return np.array(image)

# 병렬 처리
def process_image_part(part):
    part_array = pil_to_numpy(part)
    return reader.readtext(part_array)

def perform_ocr_parallel(image_parts):
    with Pool(processes=4) as pool:
        results = pool.map(process_image_part, image_parts)
    return [item for sublist in results for item in sublist]

# 메인 실행
def ocr(image_url):
    #image_url = "http://tkfile.yes24.com/Upload2/Board/202410/20241024/51467_2.jpg"
    original_image = download_image(image_url)

    # 이미지 크기 조정
    original_image = resize_image(original_image)

    # 이미지 분할
    image_parts = split_image(original_image, height_limit=1000)

    # 병렬 OCR 실행
    ocr_results = perform_ocr_parallel(image_parts)
    

    # 텍스트 추출
    texts = [result[1] for result in ocr_results]
    for idx, text in enumerate(texts, start=1):
        #print(f"{idx}. {text}")
        #print(f"{text}")
        return text

#if __name__ == "__main__":
#    main()  # 함수 호출

