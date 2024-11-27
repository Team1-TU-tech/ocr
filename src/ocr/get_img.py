import requests
from PIL import Image
from io import BytesIO
import numpy as np
import easyocr
from multiprocessing import Pool

# 이미지 다운로드
def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 실패: {e}")
        return None

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

# 병렬 처리: EasyOCR Reader를 생성하여 처리
def process_image_part(part):
    reader = easyocr.Reader(['ko', 'en'])  # Pool 내에서 Reader 생성
    part_array = pil_to_numpy(part)
    return reader.readtext(part_array)

def perform_ocr_parallel(image_parts):
    with Pool(processes=4) as pool:
        results = pool.map(process_image_part, image_parts)
    return [item for sublist in results for item in sublist]

# 메인 OCR 함수
def ocr(image_url):
    # 이미지 다운로드
    original_image = download_image(image_url)
    if original_image is None:
        return "이미지 다운로드에 실패했습니다."

    # 이미지 크기 조정
    original_image = resize_image(original_image)

    # 이미지 분할
    image_parts = split_image(original_image, height_limit=1000)

    # 병렬 OCR 실행
    ocr_results = perform_ocr_parallel(image_parts)

    # 텍스트 추출
    texts = [result[1] for result in ocr_results]
    return "\n".join(texts)  # 모든 텍스트를 합쳐 반환
