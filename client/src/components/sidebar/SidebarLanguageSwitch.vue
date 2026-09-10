<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import type { Locale } from '@bookorbit/types'
import { useLocaleStore } from '@/stores/locale'

withDefaults(defineProps<{ isRail?: boolean }>(), { isRail: false })
const { t } = useI18n()
const store = useLocaleStore()
const pending = ref(false)

async function selectLanguage(locale: Locale) {
  pending.value = true
  try {
    await store.setLocale(locale)
  } catch {
    toast.error(t('settings.appearance.language.loadError'))
  } finally {
    pending.value = false
  }
}
function selectKorean() {
  void selectLanguage('ko')
}
function selectEnglish() {
  void selectLanguage('en')
}
</script>

<template>
  <div
    class="flex gap-1 rounded-md border border-sidebar-border p-1"
    :class="isRail ? 'flex-col' : 'flex-row'"
    role="group"
    :aria-label="t('settings.appearance.language.label')"
    data-testid="sidebar-language-switch"
  >
    <button
      type="button"
      lang="ko"
      aria-label="한국어"
      :aria-pressed="store.locale === 'ko'"
      :disabled="pending"
      class="min-h-8 flex-1 rounded-sm px-1 text-xs font-medium outline-hidden transition-colors hover:bg-sidebar-accent focus-visible:ring-2 focus-visible:ring-sidebar-ring disabled:opacity-50"
      :class="store.locale === 'ko' ? 'bg-sidebar-accent text-sidebar-accent-foreground' : 'text-muted-foreground'"
      @click="selectKorean"
    >
      {{ isRail ? '한' : '한국어' }}
    </button>
    <button
      type="button"
      lang="en"
      aria-label="English"
      :aria-pressed="store.locale === 'en'"
      :disabled="pending"
      class="min-h-8 flex-1 rounded-sm px-1 text-xs font-medium outline-hidden transition-colors hover:bg-sidebar-accent focus-visible:ring-2 focus-visible:ring-sidebar-ring disabled:opacity-50"
      :class="store.locale === 'en' ? 'bg-sidebar-accent text-sidebar-accent-foreground' : 'text-muted-foreground'"
      @click="selectEnglish"
    >
      {{ isRail ? 'EN' : 'English' }}
    </button>
  </div>
</template>
