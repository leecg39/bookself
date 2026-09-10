import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import SidebarLanguageSwitch from '../SidebarLanguageSwitch.vue'
import { useLocaleStore } from '@/stores/locale'
import { storage } from '@/services/storage'

describe('sidebar language switch', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('switches languages through accessible buttons and persists the selection', async () => {
    const store = useLocaleStore()
    await store.setLocale('ko')
    const wrapper = mount(SidebarLanguageSwitch)
    expect(wrapper.get('[aria-label="한국어"]').attributes('aria-pressed')).toBe('true')
    await wrapper.get('[aria-label="English"]').trigger('click')
    await flushPromises()
    expect(store.locale).toBe('en')
    expect(storage.get('locale', '')).toBe('en')
    await wrapper.get('[aria-label="한국어"]').trigger('click')
    await flushPromises()
    expect(store.locale).toBe('ko')
    expect(storage.get('locale', '')).toBe('ko')
    wrapper.unmount()
  })

  it('keeps both language buttons available when the sidebar is collapsed', () => {
    const wrapper = mount(SidebarLanguageSwitch, { props: { isRail: true } })
    expect(wrapper.get('[aria-label="한국어"]').text()).toBe('한')
    expect(wrapper.get('[aria-label="English"]').text()).toBe('EN')
    wrapper.unmount()
  })
})
