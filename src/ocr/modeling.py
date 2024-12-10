from transformers import pipeline

# Zero-shot classification 파이프라인 사용
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# 분류할 텍스트
description = "공부하느라 축-처정던 어깨; 빨래방에서 특록 털고가세요!"

# 가능한 주제 카테고리 (사용자가 정의)
candidate_labels = ["일상", "유머", "휴식", "로맨틱", "호러", "크리스마스"]

# Zero-shot 분류 실행
result = classifier(description, candidate_labels=candidate_labels)

# 결과 출력
print(f"분류된 카테고리: {result['labels'][0]}")
print(f"확신도: {result['scores'][0]}")
