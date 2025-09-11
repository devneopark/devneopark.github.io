const BODY_SELECTOR = 'body main article figure#article-body-wrapper div#article-body-content-wrapper'
const ADDITIONAL_SELECTOR = 'body main section#additional-wrapper'

const select = selector => document.querySelector(selector)

const getPageNumber = () => {
  const param = new URLSearchParams(location.search).get('page')
  const num = parseInt(param, 10)
  return Number.isInteger(num) && num > 0 ? num : 1
}

const fetchPosts = async page => {
  try {
    const res = await fetch(`/assets/pages/posts/pages.${page}.json`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

const makePostItem = post => `
<li>
  <a class="post" href="/posts/${post.seq}" id="post-item">
    <h3>${post.title}</h3>
    <p>${post.summary}</p>
  </a>
</li>`

const makePostsBlock = posts => `
<div id="posts-wrapper">
  <ul>${posts.map(makePostItem).join('')}</ul>
</div>`

const makeLoadMoreButton = page => `<button id="load-more" data-page="${page}">더보기</button>`

const renderPosts = (container, posts) => {
  if (!posts?.length) return
  container.insertAdjacentHTML('beforeend', makePostsBlock(posts))
}

const renderLoadMore = (container, page) => {
  container.innerHTML = makeLoadMoreButton(page)
}

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

const goBack = message => { alert(message); history.back() }

document.addEventListener('DOMContentLoaded', async () => {
  const body = select(BODY_SELECTOR)
  const additional = select(ADDITIONAL_SELECTOR)
  if (!body || !additional) return

  const page = getPageNumber()
  const posts = await fetchPosts(page)
  if (!posts) {
    goBack('페이지를 찾을 수 없습니다.')
    return
  }

  renderPosts(body, posts)
  renderLoadMore(additional, page)

  additional.addEventListener('click', handleLoadMoreClick)
})
