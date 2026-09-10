import type { WritableComputedRef } from 'vue'
import { createI18n } from 'vue-i18n'
import { DEFAULT_LOCALE, LOCALE_DIRECTIONS, type Locale } from '@bookorbit/types'
import en from '@/locales/en.json'
import ko from '@/locales/ko.json'
import { compileIcuCatalog } from './icu'

export type MessageSchema = typeof en
type LocaleMessageTree = { [key: string]: string | LocaleMessageTree }

// `legacy: false` selects the Composition API overload, so `i18n.global` is a Composer
// and `i18n.global.locale` is a writable ref.
export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: 'en',
  missingWarn: false,
  fallbackWarn: false,
  messages: { en: compileIcuCatalog(en, 'en'), ko: compileIcuCatalog(ko, 'ko') },
})

const loaded = new Set<Locale>(['en', 'ko'])

export async function loadLocaleMessages(locale: Locale): Promise<void> {
  if (loaded.has(locale)) return
  const messages = (await import(`../locales/${locale}.json`)) as { default: LocaleMessageTree }
  const compiled = compileIcuCatalog(messages.default, locale)
  i18n.global.setLocaleMessage(locale, compiled as MessageSchema)
  loaded.add(locale)
}

export function activateI18nLocale(locale: Locale): void {
  ;(i18n.global.locale as WritableComputedRef<Locale>).value = locale
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('lang', locale)
    document.documentElement.setAttribute('dir', LOCALE_DIRECTIONS[locale])
  }
}

export async function setI18nLocale(locale: Locale): Promise<void> {
  await loadLocaleMessages(locale)
  activateI18nLocale(locale)
}
