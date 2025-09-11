const TAGS_SELECTOR = 'body main article figure#article-body-wrapper div#article-body-content-wrapper'
const POSTS_SELECTOR = 'body main section#additional-wrapper'

const select = selector => document.querySelector(selector)

const getParams = () => {
    const query = new URLSearchParams(location.search)
    const tag = query.get('tag')
    if (!tag) return null
    const pageRaw = query.get('page')
    const page = parseInt(pageRaw, 10)
    return {tag, page: Number.isInteger(page) && page > 0 ? page : 1}
}

const fetchTags = async () => {
    try {
        const res = await fetch('/assets/pages/tags/tags.json')
        return res.ok ? res.json() : null
    } catch {
        return null
    }
}

const fetchTagPosts = async ({tag, page}) => {
    try {
        const res = await fetch(`/assets/pages/tags/${tag}/pages.${page}.json`)
        return res.ok ? res.json() : null
    } catch {
        return null
    }
}

const makeTagItem = (tag, activeTag) => {
    if (tag === activeTag) {
        return `<li><a class="disabled" aria-disabled="true"><code>${tag}</code></a></li>`
    }
    return `<li><a href="/tags?tag=${tag}"><code>${tag}</code></a></li>`
}

const makeTagsBlock = (tags, activeTag) => `<div id="tags-wrapper"><ul>${tags.map(t => makeTagItem(t, activeTag)).join('')}</ul></div>`

const makePostItem = post => `<li><a href="/posts/${post.seq}">${post.title}</a></li>`
const makePostsBlock = posts => `<div id="tags-posts-wrapper"><ul>${posts.map(makePostItem).join('')}</ul></div>`

const makeLoadMoreButton = page => `<button id="load-more" data-page="${page}">더보기</button>`

const renderTags = (container, tags, activeTag) => {
    if (!tags?.tags?.length) return
    container.innerHTML = makeTagsBlock(tags.tags, activeTag)
}

const renderPosts = (container, posts) => {
    if (!posts?.length) return

    const existingWrapper = container.querySelector('#tags-posts-wrapper')
    if (existingWrapper) {
        const ul = existingWrapper.querySelector('ul')
        if (ul) {
            ul.insertAdjacentHTML('beforeend', posts.map(makePostItem).join(''))
            return
        }
    }

    const loadMoreButton = container.querySelector('#load-more')
    if (loadMoreButton) {
        loadMoreButton.insertAdjacentHTML('beforebegin', makePostsBlock(posts))
    } else {
        container.insertAdjacentHTML('beforeend', makePostsBlock(posts))
    }
}

const renderLoadMore = (container, page) => {
    const existing = container.querySelector('#load-more')
    if (existing) existing.remove()
    container.insertAdjacentHTML('beforeend', makeLoadMoreButton(page))
}

const handleLoadMoreClick = async event => {
    if (!event.target.matches('#load-more')) return
    const button = event.target
    const current = parseInt(button.dataset.page, 10)
    const next = current + 1

    const params = getParams()
    if (!params) return
    params.page = next

    const posts = await fetchTagPosts(params)
    if (!posts?.length) {
        button.remove()
        return
    }

    renderPosts(select(POSTS_SELECTOR), posts)
    button.dataset.page = next
}

document.addEventListener('DOMContentLoaded', async () => {
    const tagsContainer = select(TAGS_SELECTOR)
    const postsContainer = select(POSTS_SELECTOR)
    if (!tagsContainer || !postsContainer) return

    const tags = await fetchTags()
    const params = getParams()

    renderTags(tagsContainer, tags, params?.tag)

    if (!params) return

    const posts = await fetchTagPosts(params)
    if (!posts) return

    renderPosts(postsContainer, posts)
    renderLoadMore(postsContainer, params.page)

    postsContainer.addEventListener('click', handleLoadMoreClick)
})
