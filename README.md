# devneopark.github.io

[devneopark.github.io](https://devneopark.github.io)를 생성하고 배포하는 개인 블로그 프로젝트입니다. Markdown 문서를 Python으로 변환해 HTML 페이지와 JSON 인덱스를 만들고, GitHub Actions와 GitHub Pages를 통해 배포합니다.

Jekyll 같은 별도의 정적 사이트 프레임워크나 JavaScript 번들러를 사용하지 않습니다. 빌드 과정과 화면 구성을 작은 코드베이스 안에서 직접 관리합니다.

## 주요 기능

- YAML front matter가 포함된 Markdown 문서를 HTML 페이지로 변환
- fenced code block과 취소선 문법 지원
- 전체 포스트와 태그별 포스트의 페이지네이션 JSON 생성
- 홈, 포스트 목록, 태그 목록 페이지 생성
- sitemap, robots.txt와 검색 엔진 확인 파일 배치
- GitHub Actions를 통한 GitHub Pages 자동 배포

## 요구 사항

- Python 3.11 권장
- [PyYAML](https://pyyaml.org/)
- [Python-Markdown](https://python-markdown.github.io/)

## 로컬 실행

저장소를 복제하고 가상환경을 준비합니다.

```bash
git clone https://github.com/devneopark/devneopark.github.io.git
cd devneopark.github.io

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install PyYAML markdown
```

저장소 루트에서 빌드를 실행합니다.

```bash
python3 src/build.py
```

생성된 사이트는 `dist/`에서 확인할 수 있습니다. 브라우저에서 로컬로 확인하려면 간단한 HTTP 서버를 실행합니다.

```bash
python3 -m http.server 8000 --directory dist
```

이후 <http://localhost:8000>으로 접속합니다.

## 프로젝트 구조

```text
.
├── _assets/                  # 템플릿, CSS, JavaScript, 폰트, 루트 정적 파일
├── _posts/                   # Markdown 입력 문서
├── src/
│   ├── build.py              # 빌드 진입점
│   └── funcs/
│       ├── converter.py      # Markdown → HTML 변환
│       ├── html_generator.py # 템플릿 치환과 HTML 생성
│       └── parser.py         # YAML front matter 파싱
├── tests/                    # unittest 기반 테스트
├── .github/workflows/
│   └── deploy.yml            # GitHub Pages 배포
└── dist/                     # 빌드 산출물
```

## 입력 파일 형식

`_posts/`의 Markdown 파일은 YAML front matter와 본문으로 구성됩니다. 빌드에서 사용하는 필수 메타데이터는 다음과 같습니다.

```yaml
---
seq: 1
title: "제목"
summary: "요약"
tags: ["tag"]
posted_at: "2025-09-17"
---
```

- `seq`: 포스트의 고유 번호이며 `/posts/{seq}.html` 경로에 사용됩니다.
- `title`: 페이지 제목과 목록 표시에 사용됩니다.
- `summary`: 메타 태그와 목록 데이터에 사용됩니다.
- `tags`: 태그 인덱스 생성에 사용됩니다.
- `posted_at`: 게시일과 sitemap의 `lastmod`에 사용됩니다.

## 빌드 결과

`python3 src/build.py`를 실행하면 다음 산출물이 생성됩니다.

```text
dist/
├── index.html
├── posts.html
├── tags.html
├── sitemap.xml
├── robots.txt
├── googleec3a32855dc9da2c.html
├── posts/
│   └── {seq}.html
└── assets/
    ├── css/
    ├── fonts/
    ├── js/
    └── pages/
        ├── posts/
        └── tags/
```

`dist/`는 생성 디렉터리입니다. 결과물을 직접 수정하지 말고 `_posts/`, `_assets/` 또는 `src/`를 변경한 뒤 다시 빌드합니다. 빌드는 `dist/assets/`를 다시 만들지만 `dist/` 전체를 초기화하지는 않으므로, 파일을 삭제하거나 경로를 바꾼 뒤에는 오래된 산출물이 남아 있지 않은지 확인해야 합니다.

## 빌드 과정

빌드 진입점은 `src/build.py`입니다.

1. `_posts/`의 Markdown 파일을 이름순으로 읽습니다.
2. YAML front matter와 본문을 분리합니다.
3. Markdown 본문을 HTML로 변환합니다.
4. 템플릿을 이용해 포스트 페이지를 생성합니다.
5. 전체 포스트와 태그별 페이지 JSON을 생성합니다.
6. 정적 리소스와 루트 페이지, sitemap을 `dist/`에 생성합니다.

## 배포

`main` 브랜치에 push하면 `.github/workflows/deploy.yml`이 다음 작업을 수행합니다.

1. Python 3.11 환경 설정
2. `PyYAML`, `markdown` 설치
3. `python3 src/build.py` 실행
4. `dist/`를 GitHub Pages 아티팩트로 업로드
5. GitHub Pages 배포

배포 대상 저장소에서는 GitHub Pages의 Source가 **GitHub Actions**로 설정되어 있어야 합니다.

## 테스트

테스트는 Python 표준 라이브러리의 `unittest`를 사용합니다.

```bash
python3 -m unittest discover -s tests -v
```

현재 테스트는 다음 범위를 검증합니다.

- YAML front matter 파싱과 필수 메타데이터 검증
- 날짜 메타데이터 정규화
- HTML 메타데이터와 태그 URL의 이스케이프
- 페이지네이션 입력 검증
- 전체 빌드와 오래된 생성 파일 정리
