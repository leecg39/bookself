<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { BookCard } from '@bookorbit/types'
import { shelfVisual } from '../lib/shelf-layout'
import BookCoverArtwork from '@/features/book/components/BookCoverArtwork.vue'
import { useCoverVersions } from '@/features/book/composables/useCoverVersions'
const { t } = useI18n()
const props = defineProps<{ book: BookCard; index: number; selected?: boolean; selectionMode?: boolean }>()
const emit = defineEmits<{ open: [book: BookCard]; select: [id: number, event: MouseEvent] }>()
const { coverUrl } = useCoverVersions()
const visual = computed(() => shelfVisual(props.book.id, props.book.pageCount))
const style = computed(() => ({
  height: `${visual.value.height}px`,
  '--spine-width': `${visual.value.width}px`,
  backgroundColor: visual.value.color,
}))
const title = computed(() => props.book.title || t('book.untitled'))
const authors = computed(() => props.book.authors.join(', '))
function handleClick(event: MouseEvent) {
  if (props.selectionMode) emit('select', props.book.id, event)
  else emit('open', props.book)
}
</script>
<template>
  <button
    :data-shelf-index="index"
    :aria-label="`${title}${authors ? ', ' + authors : ''}`"
    :aria-pressed="selectionMode ? Boolean(selected) : undefined"
    :title="`${title}\n${authors}`"
    class="group relative [perspective:800px] flex w-full h-60 items-end justify-center focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary rounded-sm"
    @click="handleClick"
  >
    <span
      :style="style"
      class="relative flex w-22 sm:w-(--spine-width) flex-col items-center rounded-t-sm border-x border-foreground/10 text-(--shelf-ink) shadow-lg transition-transform duration-150 group-hover:[transform:translateY(-8px)_rotateY(-12deg)] group-focus-visible:[transform:translateY(-8px)_rotateY(-12deg)] motion-reduce:transform-none"
      :class="selected ? 'ring-4 ring-primary' : ''"
    >
      <span class="absolute -right-1 inset-y-1 w-1 bg-(--shelf-edge) [transform:rotateY(35deg)]" aria-hidden="true" />
      <span class="absolute inset-y-0 left-1 w-px bg-background/20" aria-hidden="true" />
      <span class="hidden sm:flex flex-1 min-h-0 py-4 text-sm font-semibold tracking-wide [writing-mode:vertical-rl] overflow-hidden">{{
        title
      }}</span>
      <span class="sm:hidden block w-full h-36 overflow-hidden">
        <BookCoverArtwork
          :src="coverUrl(book.id)"
          :has-cover="book.hasCover"
          :title="title"
          :author-line="authors"
          :seed="String(book.id)"
          :alt="title"
        />
      </span>
      <span class="sm:hidden line-clamp-2 px-1 pt-2 text-xs font-semibold">{{ title }}</span>
      <span class="mb-3 mt-2 w-full truncate border-t border-current/30 px-1 pt-2 text-[10px]">{{ authors || t('bookshelf.unknownAuthor') }}</span>
    </span>
    <span
      v-if="book.readingProgress !== null && book.readingProgress > 0"
      class="absolute bottom-0 left-1 right-1 h-1 bg-muted"
      :aria-label="t('bookshelf.progress', { percent: Math.round(book.readingProgress) })"
      ><span class="block h-full bg-primary" :style="{ width: `${Math.max(0, Math.min(100, book.readingProgress))}%` }"
    /></span>
  </button>
</template>
