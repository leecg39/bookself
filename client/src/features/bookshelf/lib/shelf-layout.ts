export const SHELF_ROW_HEIGHT = 286
export function shelfColumns(width: number) {
  return Math.max(1, Math.floor(Math.max(0, width - 32) / (width < 640 ? 112 : 76)))
}
export function shelfRange(total: number, columns: number, offset: number, height: number) {
  const count = Math.ceil(total / columns)
  const start = Math.min(count, Math.max(0, Math.floor(offset / SHELF_ROW_HEIGHT) - 1))
  const end = Math.min(count, Math.ceil((offset + height) / SHELF_ROW_HEIGHT) + 2)
  return { start, end, first: start * columns, last: Math.min(total - 1, end * columns - 1) }
}
export function shelfVisual(id: number, pageCount?: number | null) {
  const seed = Math.abs(Math.imul(id, 2654435761) >>> 0)
  return {
    height: 184 + (seed % 43),
    width: pageCount && Number.isFinite(pageCount) && pageCount > 0 ? Math.min(60, Math.max(40, 38 + pageCount / 35)) : 48,
    color: `var(--shelf-book-${seed % 5})`,
  }
}
