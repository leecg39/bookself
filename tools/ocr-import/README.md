# OCR PDF 가져오기

실제 점검에서 발견한 독립 PDF를 대상으로 합니다. Python 3.9 이상과 Poppler의 `pdfinfo`, `pdftotext`가 필요합니다. TXT/MD/JSON 변환, 재OCR, 외부 전송은 지원하지 않으며 보류 상태로 보고합니다.

## 읽기 전용 점검

```sh
python3 tools/ocr-import/import_ocr.py inventory --source /path/to/OCR --work /private/path/ocr-import
```

`inventory-report.md`와 `book-candidates.json`에서 후보와 이유를 검토합니다. 텍스트는 대표 페이지에서만 검사하며 OCR 정확도나 모든 페이지 누락까지 검증하는 것은 아닙니다. 제목은 파일명 유래의 미검증 정보이고 저자는 추정하지 않습니다. 이미지 표지 연결은 BookOrbit의 기존 PDF 처리에 따릅니다.

## 검토한 자료만 준비

```sh
python3 tools/ocr-import/import_ocr.py stage --source /path/to/OCR --work /private/path/ocr-import --ids SOURCE_UUID_1 SOURCE_UUID_2
```

원본과 다른 작업 폴더에 복사합니다. macOS에서는 `cp -c`의 APFS clone으로 물리 저장 공간을 절약하며 한쪽 변경은 다른 파일에 반영되지 않습니다. 복사 전후 해시를 비교합니다. 원본은 수정·이동·삭제하지 않습니다. `metadata.opf`에 파일명 유래 제목과 source UUID를 기록합니다. 검증되지 않은 저자·출판연도·원서 쪽수를 생성하지 않습니다.

같은 revision 재실행은 기존 복사본을 재사용합니다. 수정된 원본은 `changed_needs_review`로 보류하고 기존 파생 파일과 BookOrbit ID를 유지합니다. 본문 revision 전환은 이 도구가 자동 수행하지 않습니다. 누락 원본은 `source_missing`으로 남기며 도서를 삭제하지 않습니다. 동일 해시는 중복 후보로 표시해 자동 등록을 막습니다.

## 비공개 로컬 BookOrbit 등록

기존 계정의 인증 토큰을 환경변수로 제공하며 출력·로그에 토큰을 남기지 않습니다.

```sh
python3 tools/ocr-import/register_local.py --base-url http://127.0.0.1:3147 --work /private/path/ocr-import
```

`BOOKORBIT_TOKEN`이 필요합니다. 원격 주소와 인증 요청 리디렉션은 거절합니다. 기존 `/libraries`, `/scanner/libraries/:id/scan`, 도서 조회 API를 사용하며 별도 도서 DB를 만들지 않습니다. 최초 등록은 파생 폴더 전용 라이브러리를 생성하고 이후 `registration.json`의 라이브러리를 재사용합니다. 원본 OCR 경로를 등록하지 마세요.

등록 결과는 `manifests.json`에 sourceBookId → bookorbitBookId로 저장합니다. 페이지당 최대 100권을 조회하며 신규 ID의 상세만 확인합니다. 재실행으로 파일이나 사용자 제목·태그·독서 상태를 덮어쓰지 않습니다. 스캐너가 오래 걸리거나 연결이 끊기면 기록을 유지한 채 다시 실행할 수 있습니다. 만료된 토큰은 재로그인 후 갱신하세요.

## 검사

```sh
python3 -m unittest discover -s tools/ocr-import -p 'test_*.py'
```

작업 폴더는 인증정보·파일명·PDF가 포함된 비공개 로컬 산출물입니다. Git 및 웹 `public`에 넣지 않습니다. 단일 프로세스로 실행하며 동시에 같은 작업 폴더를 수정하지 마세요.
