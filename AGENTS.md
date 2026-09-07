# AGENTS.md

이 문서는 이 저장소에서 작업하는 AI 에이전트를 위한 실행 지침이다. 저장소 루트와 모든 하위 경로에 적용하며, 더 하위 경로에 별도의 `AGENTS.md`가 있으면 해당 문서가 우선한다. 프로젝트 소개와 사용법은 `README.md`에 둔다.

## 응답과 협업

- 사용자 응답과 저장소 내 작업 문서는 한글을 우선한다.
- 작업 전 `git status --short`와 관련 파일을 확인한다.
- 중요한 변경을 시작하기 전에 목적과 예상 영향 범위를 짧게 공유한다.
- 요구가 명확하면 합리적인 가정으로 진행하되, 공개 URL 변경·대규모 삭제·배포 방식 변경처럼 결과가 크게 달라지는 선택은 먼저 확인한다.
- 사용자의 기존 변경과 무관한 파일은 수정하거나 되돌리지 않는다.
- 완료 보고에는 변경 파일, 핵심 결과, 실행한 검증과 남은 위험을 포함한다.

## 프로젝트 개요

Python으로 구현한 개인 블로그용 정적 사이트 생성기다. 별도의 프론트엔드 프레임워크나 JavaScript 빌드 단계는 없다.

- `_posts/`: 빌드 입력 Markdown 문서
- `_assets/`: HTML 템플릿, CSS, ES 모듈 JavaScript, 폰트와 루트 정적 파일
- `src/build.py`: 전체 빌드 진입점
- `src/funcs/parser.py`: YAML front matter와 본문 분리
- `src/funcs/converter.py`: Markdown을 HTML로 변환
- `src/funcs/html_generator.py`: 템플릿 치환과 HTML 파일 생성
- `tests/`: 표준 `unittest` 기반 회귀·통합 테스트
- `.github/workflows/deploy.yml`: GitHub Pages 배포 워크플로우
- `dist/`: 빌드 산출물. Git에서 제외되는 생성 디렉터리

## 원본과 생성물

- 수정의 원본은 `_posts/`, `_assets/`, `src/`와 저장소 설정 파일이다.
- `dist/`를 직접 수정하지 않는다. 필요한 변경은 원본에 적용한 뒤 다시 빌드한다.
- `_assets/template.html`의 `${title}`, `${head.tags}`, `${jss}`, `${article.header}`, `${article.content}`는 빌드 코드와 연결된 계약이다. 변경할 때 생성기 코드를 함께 확인한다.
- 문서 메타데이터의 `seq`, `title`, `summary`, `tags`, `posted_at`은 빌드 과정에서 사용된다. 키 이름이나 형식을 바꾸려면 파서, 생성기, 인덱스 JSON과 공개 URL 영향을 모두 검토한다.
- 포스트 공개 경로 `/posts/{seq}.html`, 목록 경로 `/posts.html`, 태그 경로 `/tags.html`을 호환성 검토 없이 변경하지 않는다.
- 사이트 기준 URL은 `src/build.py`의 `SITE_URL`이며 sitemap 생성에 사용된다.

## 빌드 흐름

`python3 src/build.py`는 다음 작업을 수행한다.

1. `_posts/`의 파일을 이름순으로 읽는다.
2. YAML front matter와 Markdown 본문을 파싱한다.
3. `dist/posts/{seq}.html`을 생성한다.
4. 포스트 목록과 태그별 페이지 JSON을 `dist/assets/pages/`에 생성한다.
5. `_assets/`를 `dist/assets/`로 복사하고 배포 위치가 다른 루트 파일을 이동한다.
6. `dist/index.html`, `dist/posts.html`, `dist/tags.html`, `dist/sitemap.xml`을 생성한다.

`dist/assets/`는 빌드 중 정리되지만 `dist/` 전체가 초기화되지는 않는다. 파일 삭제나 경로 변경을 검증할 때는 오래된 산출물이 남을 가능성을 고려한다.

## 개발 환경

권장 환경은 배포 워크플로우와 같은 Python 3.11이다. 런타임 의존성은 `PyYAML`과 `markdown`이다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install PyYAML markdown
python3 -m unittest discover -s tests -v
python3 src/build.py
```

의존성 선언 파일은 현재 없다. 새 의존성을 추가할 때는 로컬 설치 방법과 `.github/workflows/deploy.yml`을 함께 갱신해야 한다.

## 구현 규칙

- 요청을 해결하는 데 필요한 최소 범위로 변경한다.
- Python은 기존 모듈 구조와 4칸 들여쓰기를 유지하고, 파일 입출력 시 UTF-8을 명시한다.
- 경로 처리 방식은 기존 `os.path` 기반 코드와 일관되게 유지한다. 전면적인 스타일 변경은 별도 요청이 있을 때만 수행한다.
- JavaScript는 브라우저에서 직접 실행되는 ES 모듈이다. Node.js 전용 API나 번들러 전제를 추가하지 않는다.
- 템플릿과 생성기에 삽입되는 값의 HTML 이스케이프 여부를 확인한다. 사용자 제어 값이 속성이나 마크업에 들어가면 안전성을 검토한다.
- 파일 순서, `seq`, 페이지 크기와 정렬 로직을 변경할 때 목록·태그·URL에 미치는 영향을 함께 확인한다.
- 임시 디버깅 코드, 사용하지 않는 주석, 로컬 절대 경로를 남기지 않는다.

## 공개 저장소 안전 기준

- 비밀값, 토큰, 인증정보, 개인 데이터와 로컬 전용 설정을 커밋하지 않는다.
- 특정 AI 도구의 로컬 설정, 비공개 작업 지침, 개인 메모를 저장소에 추가하지 않는다.
- 새 파일을 만들기 전에 `.gitignore` 적용 여부와 공개되어도 되는 내용인지 확인한다.
- 외부 리소스나 액션 버전을 추가할 때 출처, 필요 권한과 배포 영향을 확인한다.
- 생성 파일, 에디터 설정, 캐시와 가상환경은 저장소에 포함하지 않는다.

## 검증

변경 범위에 맞춰 다음 검증을 수행한다.

- 문서 또는 설정만 변경: 문법, 경로와 실제 저장소 구조를 대조한다.
- Python 또는 빌드 로직 변경: `python3 -m unittest discover -s tests -v`와 `python3 src/build.py`를 실행하고 종료 코드와 생성 파일을 확인한다.
- 템플릿·CSS·JavaScript 변경: 빌드 후 관련 HTML과 정적 파일을 확인하고, 필요하면 로컬 서버에서 화면과 브라우저 콘솔을 점검한다.
- 메타데이터·정렬·페이지네이션 변경: 포스트 HTML, 목록 JSON과 태그 JSON을 표본 확인한다.
- sitemap·robots·검색 노출 변경: `dist/sitemap.xml`, `dist/robots.txt`와 기준 URL을 확인한다.
- 배포 워크플로우 변경: YAML 문법, Python 버전, 의존성 설치, `dist` 아티팩트 경로와 권한을 확인한다.

빌드가 성공해도 생성된 HTML의 의미적 오류나 브라우저 동작까지 보장되지는 않는다. 사용자에게 영향을 주는 화면 변경은 가능한 범위에서 직접 확인한다. 검증하지 못한 항목은 완료 보고에 이유와 함께 명시한다.

## 배포

`main` 브랜치 push 시 `.github/workflows/deploy.yml`이 Python 3.11 환경에서 사이트를 빌드하고 `dist/`를 GitHub Pages 아티팩트로 배포한다.

- 배포 명령을 바꾸면 로컬 빌드 절차와 일치하는지 확인한다.
- `dist/` 산출 경로와 Pages 업로드 경로를 함께 유지한다.
- Actions 권한과 GitHub Pages 설정을 필요 이상으로 확대하지 않는다.
- 도메인, 기준 URL, 공개 경로 또는 배포 트리거 변경은 사용자 확인 후 진행한다.

## 결과 보고

- 완료 시 변경 목적, 수정한 파일, 검증 명령과 결과, 남은 문제를 간결하게 보고한다.
- 파일 삭제가 있었다면 삭제 대상과 복구 가능 여부를 함께 알린다.
