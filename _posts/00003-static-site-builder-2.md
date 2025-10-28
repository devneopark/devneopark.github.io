---
seq: 3
title: "정적 사이트 빌더 구축기(with. GitHub Pages) - 下"
summary: "구현 구조와 빌드/배포 흐름을 정리하고, 시행착오를 기록합니다."
tags: [ "github", "python", "static-site-generator" ]
posted_at: "2025-10-28"
---

> ### 시리즈
> [정적 사이트 빌더 구축기(with. GitHub Pages) - 上](https://devneopark.github.io/posts/2.html)   
> 정적 사이트 빌더 구축기(with. GitHub Pages) - 下 - 현재 포스트

# 이어서, 구현 이야기

상편에서 "직접 만들겠다"는 결정을 적었습니다.
이번에는 전반적인 빌드 엔진(?)의 구조와 중간에 있었던 시행착오를 소개하려고 합니다.

# 디렉토리 구조

구조는 네 개 큰 디렉토리로 끝냈습니다.

- `_posts/`: yml 프론트매터가 있는 마크다운 포스트
- `_assets/`: 템플릿, css/js, 정적 리소스
- `src/`: 빌드 스크립트와 파서/생성기
- `dist/`: 최종 산출물

처음에는 "기능을 더 넣어야 하나"를 계속 고민했습니다.
이렇다할 아이디어도 마땅히 떠오르지 않았고, 굳이 많은 기능 구현에 힘을 쏟고싶지도 않았습니다.
"블로그에 필요한 최소 흐름만 남기자"고 기준을 잡고 나니 디테일한 기능과 간단한 디렉토리 구조만으로 정리됐습니다.

# 전체 빌드 흐름

콘텐츠 빌드 시작점은 `src/build.py` 입니다. 모든 작업 과정은 main 함수에서 순차적으로 진행됩니다.
전체 흐름이 한눈에 보이게 만드는 게 목표였습니다.

```python
# src/build.py
# 이 함수만 읽어도 전체 흐름이 보이도록 구성

def main():
    print("build started.")
    ensure_dir(DIST_DIR)

    # 1) 템플릿 로딩
    html_template = read_text(os.path.join(ASSETS_DIR, "template.html"))

    # 2) 포스트 HTML 생성 + 태그 맵 구축
    posts_meta, tags_map = build_post_pages(html_template)
    posts_meta = list(reversed(posts_meta))

    # 3) 태그별 최신순 정렬
    tags_map = {
        tag: sorted(metas, key=lambda m: m["seq"], reverse=True)
        for tag, metas in tags_map.items()
    }

    # 4) 정적 리소스 복사
    copy_assets_clean()

    # 5) 인덱스/태그 JSON 생성
    write_posts_index_pages(posts_meta)
    write_tag_index_pages(tags_map)
    write_tags_list_file(tags_map)

    # 6) 홈/목록 정적 페이지 생성
    build_static_pages(html_template)

    print("build done.")
```

이 순서를 잡는 데 시간이 걸렸습니다. 빌드 순서가 엇갈리면 결과물이 줄줄이 깨졌습니다. 그때부터는 "흐름을 한 번에 끝내자"로 마음을 바꿨습니다. 순서를 고정해두니 실수가 줄었습니다.

# 마크다운 포스트 파싱

프론트매터는 지킬같은 마크다운 위주의 템플릿엔진이나 옵시디언에서 자주 사용되는 패턴입니다.
참고한 여러 레퍼런스에서는 다음과 같이 일종의 메타데이터를 작성하는 구역으로 사용됐습니다.
처음에는 막상 메타데이터를 지정하려고 별도의 .json 같은 파일을 추가하려했는데, 프론트매터로 훨씬 편하게 관리할 수 있었습니다.

```plaintext
---
title: "문서의 제목",
date: "2025-01-01",
...
---
```

프론트매터가 달린 마크다운 포스트를 파싱할때 yml 블록과 본문을 분리해 메타데이터는 별도의 .json파일로, 본문은 템플릿 엔진으로 던집니다.
처음에는 yml 블록을 정규식으로 처리하려 했는데, 생각보다 엣지케이스를 잡을수록 예외가 늘었습니다.
그래서 복잡하게 생각하지말고 그냥 첫 `---`과 두번째 `---` 사이에는 무조건 프론트매터가 온다고 가정하고 처리하자로 방향을 바꿨습니다.

```python
# src/funcs/parser.py
# 프론트매터와 본문을 분리해 meta/body로 반환

def parse(file_path: str):
    yml_lines = []
    body_lines = []
    in_yml = False
    yml_parsed = False

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "---":
                if not in_yml and not yml_parsed:
                    in_yml = True
                    continue
                elif in_yml:
                    in_yml = False
                    yml_parsed = True
                    continue

            if in_yml:
                yml_lines.append(line)
            else:
                body_lines.append(line)

    meta = {}
    if yml_lines:
        meta = yaml.safe_load("".join(yml_lines)) or {}

    body_text = "".join(body_lines).strip()
    return meta, body_text
```

이 방향으로 바꾼 뒤 메타데이터가 비어 나오던 문제도 해결했습니다. 파싱 로직이 단순해지니 디버깅도 쉬웠습니다.

# HTML 생성하기

_assets 디렉토리에 페이지 생성에 사용할 `template.html`을 만들어두고 정해진 문자열을 치환합니다.
크게 헤더, 본문으로 나뉘고 본문 안에서는 페이지 헤더와 페이지 콘텐츠로 구역을 정하고 페이지 메타데이터를 입력하기위해 <head>태그 안에 프론트매터에서 읽어온 정보를 채워넣습니다.

```python
# src/funcs/html_generator.py
# 메타데이터와 본문을 템플릿에 끼워 넣는다

def generate_post(html_path, html_template, body_html, meta: dict, jss: str = ""):
    template = html_template

    # head 태그 구성
    template = template.replace("${title}", meta["title"])
    head_tags = (
        f'<meta name="Date" content="{meta["posted_at"]}">\n'
        f'    <meta name="Keywords" content="{meta["title"]}">\n'
        f'    <meta name="Keywords" content="{meta["summary"]}">\n'
        f'    <meta name="Description" content="{meta["summary"]}">'
    )
    template = template.replace("${head.tags}", head_tags)

    # 스크립트 주입
    template = template.replace("${jss}", jss or "")

    # 헤더 + 본문 삽입
    article_header = (
        f"<h1>{meta['title']}</h1>\n"
        f"{_render_tags_ul(meta.get('tags', []))}\n"
        f"<p>{meta['posted_at']}</p>"
    )
    template = template.replace("            ${article.header}", article_header)
    template = template.replace("                ${article.content}", body_html)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)
```

# 페이징 처리와 태그 화면

여러 지킬 템플릿을 뒤적이면서 페이징과 태그 모아보기를 어떻게 처리했는지 먼저 봤습니다.
대부분은 목록 페이지까지 html로 뽑고 `/pages/2/`처럼 디렉토리를 쌓았습니다.
굳이 목록 화면까지 html로 만들어야하나 싶어 포스트 목록은 .json으로 만들고 화면에서 불러오도록 바꿨습니다.

```python
# src/build.py
# 페이지 사이즈만큼 끊어서 목록을 분할

PAGE_SIZE = 10

def paginate(items, size: int):
    n = len(items)
    i = 0
    page = 1
    while i < n:
        yield page, items[i:i + size]
        i += size
        page += 1
```

목록에 담길 json 구조는 단순하게 유지합니다. 화면에서 필요한 필드만 넣었습니다.

```json
# dist/assets/pages/posts/pages.1.json

[
    {
        "seq": 2,
        "title": "두번째 포스트",
        "summary": "두번째 포스트 요약",
        "tags": [],
        "posted_at": "2025-09-17",
        "filename": "00002-second.md"
    },
    {
        "seq": 1,
        "title": "첫번째 포스트",
        "summary": "첫번째 포스트",
        "tags": [
            "etc"
        ],
        "posted_at": "2025-01-01",
        "filename": "00001-first-post.md"
    }
]
```

태그 화면도 같은 구조로 가고 싶었습니다.
태그만 모아둔 .json, 각 태그가 달린 포스트 목록의 페이지 .json을 만들어 화면에서 필요한 것만 읽게 했습니다.
페이징은 별도 파라미터가 없는 경우에 첫 페이지번호를 `1`로 읽고, 그 다음부터는 “더보기” 버튼에 `data-page`만 두고 값을 늘립니다.

```javascript
// _assets/js/posts.mjs
// 초기 page는 URL에서 읽고, 이후는 로컬 상태로만 증가

const makeLoadMoreButton = page => `<button id="load-more" data-page="${page}">더보기</button>`

const handleLoadMoreClick = async event => {
  if (!event.target.matches('#load-more')) return

  const button = event.target
  const current = parseInt(button.dataset.page, 10)
  const next = current + 1

  const posts = await fetchPosts(next)
  if (!posts?.length) {
    button.remove()
    return
  }

  renderPosts(select(BODY_SELECTOR), posts)
  button.dataset.page = next
}
```

# 정적 리소스 복사

`_assets`는 그대로 `dist/assets`로 `template.html`만 제외하고 복사합니다.
GitHub Actions에서는 특정 디렉토리만 배포할 수 있어 배포할 산출물만 모아두었습니다.

```python
# src/build.py
# 템플릿은 제외하고 정적 리소스만 복사

def copy_assets_clean() -> None:
    if os.path.exists(DIST_ASSETS_DIR):
        shutil.rmtree(DIST_ASSETS_DIR)
    shutil.copytree(ASSETS_DIR, DIST_ASSETS_DIR)
    tpl_path = os.path.join(DIST_ASSETS_DIR, "template.html")
    if os.path.exists(tpl_path):
        os.remove(tpl_path)
```

# 꼭 필요한 기능만 남기기

필수 기능은 게시글 페이징과 태그 모아보기로 제한했습니다.
태그 페이지에서도 페이징이 되도록 했습니다.
그 외 기능은 아이디어가 더 필요했고, 지금은 미뤄둔 상태입니다.
지금의 목적은 "다시 기록하기"였고, 기능보다 흐름을 먼저 만들고 싶었습니다.

# 앞으로 개선할 요소들

개선 요소들은 실제로 고려 중입니다.
다만 이제는 손으로 일일이 작성하기보다 Codex와 함께 해보려합니다.

- 변경된 포스트만 재빌드하기 - 빌드 최적화
- 여러 포스트를 동시에 처리하기 - 비동기 io 처리

# 마무리

하편까지 적고 나니 선택한 지점이 더 또렷하게 보였습니다.
거창한 프로젝트는 아니지만, 내 기록을 내 방식으로 굴릴 수 있게 됐다는 점이 제일 만족스럽습니다.
당장은 지금 흐름을 유지하면서 글을 더 쌓고 다음 개선은 여유가 생겼을 때 필요한 만큼만 천천히 만져볼 생각입니다.
