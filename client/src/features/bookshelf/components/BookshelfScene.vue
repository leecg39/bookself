<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { BookCard } from '@bookorbit/types'
import { isBookPlaceholder, type BookSlot } from '@/features/book/composables/useBookWindow'
import { useShelfLayout } from '../composables/useShelfLayout'
import { SHELF_ROW_HEIGHT } from '../lib/shelf-layout'
import ShelfBook from './ShelfBook.vue'
const props = defineProps<{ books: BookSlot[]; viewport: HTMLElement | null; selectionMode?: boolean; isSelected?: (id: number) => boolean }>()
const emit = defineEmits<{
  range: [start: number, end: number]
  action: [book: BookCard, action: 'quick-view']
  select: [id: number, event: MouseEvent]
}>()
const element = ref<HTMLElement | null>(null)
const { columns, range, rows, focusIndex } = useShelfLayout(
  element,
  () => props.viewport,
  () => props.books.length,
)
const size = computed(() => ({ height: `${Math.ceil(props.books.length / columns.value) * SHELF_ROW_HEIGHT}px` }))
watch(
  range,
  (value) => {
    if (value.last >= value.first) emit('range', value.first, value.last)
  },
  { immediate: true },
)
function rowStyle(row: number) {
  return { top: `${row * SHELF_ROW_HEIGHT}px`, height: `${SHELF_ROW_HEIGHT}px`, gridTemplateColumns: `repeat(${columns.value}, minmax(0, 1fr))` }
}
function rowBooks(row: number) {
  return props.books.slice(row * columns.value, (row + 1) * columns.value)
}
function open(book: BookCard) {
  emit('action', book, 'quick-view')
}
function select(id: number, event: MouseEvent) {
  emit('select', id, event)
}
defineExpose({ focusIndex, scrollToIndex: focusIndex })
</script>
<template>
  <div class="rounded-xl bg-(--shelf-paper) px-2 sm:px-6 pt-5 pb-8 text-foreground">
    <div class="flex items-baseline justify-between gap-3 px-2 pb-5 border-b border-(--shelf-wood)/30">
      <h2 class="font-serif text-2xl sm:text-3xl">나의 책장</h2>
      <span class="text-xs text-muted-foreground">책을 골라 펼쳐보세요</span>
    </div>
    <div ref="element" class="relative" :style="size" aria-label="도서 책장">
      <div
        v-for="row in rows"
        :key="row"
        class="absolute inset-x-0 grid items-end gap-1 px-3 pb-7 border-x-8 border-(--shelf-wood)"
        :style="rowStyle(row)"
      >
        <div v-for="(book, index) in rowBooks(row)" :key="book.id" class="min-w-0">
          <div v-if="isBookPlaceholder(book)" class="mx-auto h-48 w-10 bg-muted motion-safe:animate-pulse" aria-label="도서 불러오는 중" />
          <ShelfBook
            v-else
            :book="book"
            :index="row * columns + index"
            :selection-mode="selectionMode"
            :selected="isSelected?.(book.id)"
            @open="open"
            @select="select"
          />
        </div>
        <div
          aria-hidden="true"
          class="absolute bottom-0 inset-x-0 h-7 border-t-4 border-(--shelf-edge) bg-(--shelf-wood) bg-[repeating-linear-gradient(2deg,transparent,transparent_4px,var(--shelf-grain)_5px,transparent_6px)] shadow-lg"
        />
      </div>
    </div>
  </div>
</template>
