import { describe, expect, it } from 'vitest'
import { DEFAULT_LOCALE } from '@bookorbit/types'
import en from '@/locales/en.json'
import ko from '@/locales/ko.json'
import { SETTINGS_NAV, type SettingsNavItem } from '@/features/settings/lib/settings-nav'
import { i18n, setI18nLocale } from './index'

function lookup(key: string): unknown {
  return key.split('.').reduce<unknown>((node, segment) => (node as Record<string, unknown> | undefined)?.[segment], ko)
}

function catalogKeys(source: Record<string, unknown>, prefix: string): string[] {
  return Object.entries(source).flatMap(([key, value]) => {
    const path = `${prefix}.${key}`
    return typeof value === 'string' ? [path] : catalogKeys(value as Record<string, unknown>, path)
  })
}

function itemKeys(item: SettingsNavItem): string[] {
  return [item.labelKey, ...(item.descriptionKey ? [item.descriptionKey] : []), ...(item.children?.flatMap(itemKeys) ?? [])]
}

describe('Korean interface', () => {
  it('ships Korean translations for every navigation item, title, shared menu and login message', () => {
    expect(DEFAULT_LOCALE).toBe('ko')
    const required = [
      ...catalogKeys(en.components, 'components'),
      ...catalogKeys(en.titles, 'titles'),
      ...catalogKeys(en.auth, 'auth'),
      ...catalogKeys(en.reader.pdf.controls, 'reader.pdf.controls'),
      ...SETTINGS_NAV.flatMap((group) => [group.labelKey, ...group.items.flatMap(itemKeys)]),
    ]
    expect(required.filter((key) => typeof lookup(key) !== 'string')).toEqual([])
  })

  it('activates both bundled languages and formats Korean ICU counts', async () => {
    await setI18nLocale('ko')
    expect(document.documentElement.lang).toBe('ko')
    expect(i18n.global.t('components.sidebar.dashboard')).toBe('대시보드')
    expect(i18n.global.t('components.appHeader.bookCount', { count: 3 })).toBe('도서 3권')
    await setI18nLocale('en')
    expect(document.documentElement.lang).toBe('en')
    expect(i18n.global.t('components.sidebar.dashboard')).toBe('Dashboard')
  })
})
