# 학급 기초자료 조사서 원스캔 OCR 취합 프로그램

Windows 로컬 PC에서 **인터넷 없이** 실행되는 PyQt5 데스크톱 앱입니다. 학급 전체 스캔 PDF를 페이지(또는 묶음) 단위로 나누고, `form_template.json`의 고정 좌표로 Tesseract OCR을 수행한 뒤 **교사 검수**를 거쳐 `master.xlsx`로 취합합니다.

## 1. 프로그램 목적

- 프로그램이 만든 **OCR 친화적 표준 양식 PDF**와 `form_template.json`을 동시에 생성합니다.
- 학부모가 작성한 조사서를 **한 번에 스캔한 PDF**를 불러와 페이지별로 학생 자료를 분리합니다.
- 좌표 기반 OCR 후 **자동 확정 없이** 검수 UI에서 수정합니다.
- 알레르기·천식 등 **보건 키워드**와 위험도(high/medium/low)를 표시하고 엑셀에 반영합니다.

## 2. 설치 방법

- Python **3.11 이상** 권장 (3.10에서도 동작 확인 가능).
- [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) 설치.
- 한국어 데이터 `kor.traineddata`가 `tessdata` 폴더에 있어야 합니다.

```powershell
cd student_info_one_scan_ocr_app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. 실행 방법

```powershell
cd student_info_one_scan_ocr_app
python main.py
```

실행 폴더 아래에 `config`, `templates`, `output`, `logs`, `temp`가 자동 생성됩니다.

## 4. 표준 조사서 양식 생성

1. 메뉴/툴바 **「표준 양식 만들기」** 실행.
2. 학년도, 학교명, 학년, 반, 담임명, 제출기한 및 동의/QR 옵션 입력.
3. `output` 폴더에 다음이 생성됩니다.
   - `학생기초자료조사서_양식.pdf`
   - `form_template.json` (필드별 `bbox_ratio` 포함)
   - `printable_form_preview.png`

## 5. 학부모 배부 및 회수

- 생성된 PDF를 출력하여 학부모에게 배부합니다.
- 회수 후 담임이 **학급 전체**를 한 번에 스캔해 **PDF 1개**로 만듭니다.

## 6. 학급 전체 PDF 스캔 방법

- 복합기에서 **멀티페이지 PDF**로 저장합니다.
- 기본 원칙: **PDF 1페이지 = 학생 1명**(또는 설정한 `pages_per_student` 묶음).

## 7. 스캔 권장 조건

- **300dpi 이상** 권장(설정에서 변경 가능).
- **검은색 펜** 사용 권장.
- 학생 1명당 1페이지(또는 2페이지형 양식이면 2페이지 묶음).
- 여러 학생을 하나의 PDF로 스캔 가능.
- 순서가 섞일 수 있으니 OCR 후 **번호/이름**으로 정렬·검수하세요.

## 8. Tesseract 설치 및 경로 설정

- 기본 경로 예: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **설정** 대화상자에서 실행 파일 경로를 지정합니다.
- 미설치 시 프로그램은 실행되지만 **OCR 실행**이 비활성화됩니다.

## 9. 한국어 OCR 데이터 설정

- `kor.traineddata`가 없으면 경고가 표시됩니다.
- `TESSDATA_PREFIX`가 필요한 환경이면, Tesseract 설치 루트의 상위(`tessdata`의 부모)를 환경 변수로 설정합니다. (설정 화면 안내 참고)

## 10. OCR 결과 검수 방법

- 좌측 목록에서 학생(페이지 묶음) 선택.
- 중앙에 스캔 이미지, 우측에 필드별 OCR 결과를 수정합니다.
- **검수완료** 시 상태가 갱신됩니다. **다음 미검수**로 이동할 수 있습니다.

## 11. 학급 명단 Excel 대조 방법

- 명단 파일에 **학년, 반, 번호, 성명** 열이 있어야 합니다.
- **학급 명단 불러오기** 후 OCR을 실행하면 대조 결과가 엑셀 `roster_compare` 시트에 기록됩니다.
- 유사 이름은 **자동 확정하지 않으며** 검토가 필요할 수 있습니다.

## 12. 보건 키워드 사전 수정 방법

- `config/keyword_dictionary.json`을 편집합니다.
- 카테고리·`risk_high`·`risk_medium` 목록을 조정할 수 있습니다.

## 13. Excel 출력 설명

- **엑셀 저장** 시 개인정보 경고 후 `output` 폴더에 저장됩니다.
- 시트: `normalized`, `health_review`, `page_review_status`, `roster_compare`, `raw_ocr`, `keyword_flags`, `errors`, `settings_snapshot`

## 14. 개인정보 및 민감정보 보호 유의사항

- 원본 PDF/이미지는 **수정하지 않습니다**.
- 로그에는 **이름·전화·주소 원문**을 남기지 않도록 마스킹합니다.
- 임시 파일은 설정에 따라 종료 시 삭제할 수 있습니다(향후 옵션 확장).

## 15. 손글씨 OCR 한계

- 손글씨 인식은 환경·필기에 따라 오류가 큽니다. **교사 검수**가 필수입니다.
- confidence가 낮거나 필수 필드가 비면 **검토필요**로 표시됩니다.

## 16. 자주 발생하는 오류 해결 방법

| 증상 | 조치 |
|------|------|
| OCR 버튼 비활성 | Tesseract 경로 및 `kor.traineddata` 확인 |
| PDF 로드 실패 | 파일 손상·경로·권한 확인 |
| 엑셀 저장 실패 | 파일이 Excel에서 열려 있는지, 쓰기 권한 확인 |

## 17. PyInstaller 빌드 방법

```powershell
cd student_info_one_scan_ocr_app
pip install pyinstaller
pyinstaller --clean build.spec
```

- `dist\StudentInfoOneScanOCR.exe` 가 생성됩니다(단일 실행 파일 구성).
- **Tesseract는 별도 설치**해야 하며, 사용자 PC에 `tessdata`가 있어야 합니다.

## 테스트

```powershell
python -m pytest tests -q
```

## 라이선스

교육 현장 내부 사용을 전제로 한 예제 프로젝트입니다. 실제 운영 시 학교·교육청 개인정보 처리방침을 준수하세요.
