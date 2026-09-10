import { describe, expect, it } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import type { BookCard } from '@bookorbit/types'
import BookshelfScene from '../components/BookshelfScene.vue'
import ShelfBook from '../components/ShelfBook.vue'

function book(id: number): BookCard {
  return { id, title: `한글 도서 ${id}`, authors: [], hasCover: false, pageCount: null, readingProgress: null } as unknown as BookCard
}

describe('bookshelf integration', () => {
  it('renders a bounded set and requests only the visible range for 10000 slots', () => {
    const books = Array.from({ length: 10000 }, (_, index) => book(index + 1))
    const wrapper = shallowMount(BookshelfScene, { props: { books, viewport: null } })
    const rendered = wrapper.findAllComponents(ShelfBook)
    expect(rendered.length).toBeGreaterThan(0)
    expect(rendered.length).toBeLessThan(100)
    expect(wrapper.emitted('range')?.[0]).toEqual([0, rendered.length - 1])
    expect(rendered.map((item) => item.props('book').id)).toEqual(books.slice(0, rendered.length).map((item) => item.id))
    wrapper.unmount()
  })
  it('routes selection separately from opening a book', async () => {
    const wrapper = shallowMount(ShelfBook, { props: { book: book(27), index: 0, selectionMode: true } })
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('select')?.[0]?.[0]).toBe(27)
    expect(wrapper.emitted('open')).toBeUndefined()
    await wrapper.setProps({ selectionMode: false })
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('open')?.[0]?.[0]).toMatchObject({ id: 27 })
    wrapper.unmount()
  })
})
