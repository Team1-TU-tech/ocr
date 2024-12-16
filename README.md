# Yes24 티켓 공연정보 이미지 OCR 텍스트 추출
이 프로젝트는 이미지에서 텍스트를 추출하는 OCR(Optical Character Recognition) 기능을 제공합니다. 해당 기능은 `easyocr` 라이브러리를 사용하여 이미지를 처리하고 텍스트를 추출합니다.
<br></br>
## 기술스택
<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=Python&logoColor=F5F7F8"/>   <img src="https://img.shields.io/badge/numpy-013243?style=flat&logo=numpy&logoColor=F5F7F8"/>    <img src="https://img.shields.io/badge/mongodb-47A248?style=flat&logo=mongodb&logoColor=F5F7F8"/> 
<br></br>
## 개발기간
`2024.11.21 ~ 2024.11.25 (총 5일)`
<br></br>
## 기능설명
- 이미지를 로드하여 OCR을 사용해 텍스트를 추출
- 다양한 이미지 포맷 지원 (JPEG, PNG, TIFF 등)
- 추출된 텍스트를 파일로 저장하거나 콘솔에 출력
- 텍스트 추출 정확도 개선을 위한 기본 이미지 전처리 기능 제공
- 이미지 전처리 후 MongoDB에 데이터 적재
<br></br>
## 이미지 전처리 (선택사항)
OCR의 정확도를 높이기 위해 이미지를 전처리할 수 있습니다. 다음과 같은 전처리 옵션을 사용할 수 있습니다:

- 이미지 크기 조정
- 이미지 분할 (큰 이미지의 경우)

```python
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
```
<br></br>
## Contributors
`hamsunwoo`
<br></br>
## License
이 애플리케이션은 TU-tech 라이선스에 따라 라이선스가 부과됩니다.
<br></br>
## 문의
질문이나 제안사항이 있으면 언제든지 연락주세요:
- 이메일: TU-tech@tu-tech.com
- Github: `Mingk42`, `hahahellooo`, `hamsunwoo`, `oddsummer56`
