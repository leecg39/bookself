import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { useElementSize, useEventListener } from '@vueuse/core'
import { shelfColumns, shelfRange, SHELF_ROW_HEIGHT } from '../lib/shelf-layout'

export function useShelfLayout(element: Ref<HTMLElement | null>, viewport: () => HTMLElement | null, total: () => number) {
  const { width } = useElementSize(element)
  const offset = ref(0)
  const height = ref(800)
  const columns = computed(() => shelfColumns(width.value))
  function measure() {
    const parent = viewport()
    if (!parent || !element.value) return
    offset.value = Math.max(0, parent.getBoundingClientRect().top - element.value.getBoundingClientRect().top)
    height.value = parent.clientHeight
  }
  useEventListener(viewport, 'scroll', measure, { passive: true })
  useEventListener(window, 'resize', measure)
  const range = computed(() => shelfRange(total(), columns.value, offset.value, height.value))
  const rows = computed(() => Array.from({ length: Math.max(0, range.value.end - range.value.start) }, (_, i) => range.value.start + i))
  watch([width, total], measure, { flush: 'post' })
  let timer: ReturnType<typeof setTimeout> | undefined
  function focusIndex(index: number) {
    const parent = viewport()
    if (!parent || !element.value) return
    const top = parent.scrollTop + element.value.getBoundingClientRect().top - parent.getBoundingClientRect().top
    const rowTop = top + Math.floor(index / columns.value) * SHELF_ROW_HEIGHT
    if (rowTop < parent.scrollTop || rowTop + SHELF_ROW_HEIGHT > parent.scrollTop + parent.clientHeight) parent.scrollTop = rowTop
    measure()
    clearTimeout(timer)
    timer = setTimeout(() => element.value?.querySelector<HTMLButtonElement>(`[data-shelf-index="${index}"]`)?.focus({ preventScroll: true }), 50)
  }
  onBeforeUnmount(() => clearTimeout(timer))
  return { columns, range, rows, focusIndex }
}
