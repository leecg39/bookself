import { describe, expect, it } from 'vitest'
import { shelfColumns, shelfRange, shelfVisual } from '../lib/shelf-layout'

describe('bookshelf layout', () => {
  for (const total of [0, 1, 100, 1000, 10000]) {
    it(`covers every index exactly once for ${total} books`, () => {
      const cols = shelfColumns(1440)
      const indices = Array.from({ length: Math.ceil(total / cols) }, (_, row) =>
        Array.from({ length: Math.min(cols, total - row * cols) }, (_, col) => row * cols + col),
      ).flat()
      expect(indices).toEqual(Array.from({ length: total }, (_, i) => i))
      const range = shelfRange(total, cols, 0, 800)
      expect(range.last - range.first + 1).toBeLessThanOrEqual(cols * 5)
    })
  }
  it('maps distant scroll positions to bounded inclusive loading ranges', () => {
    const range = shelfRange(10000, 10, 28600, 572)
    expect(range).toEqual({ start: 99, end: 104, first: 990, last: 1039 })
  })
  it('keeps mobile targets usable and visual identity stable', () => {
    expect(shelfColumns(360)).toBe(2)
    expect(shelfColumns(0)).toBe(1)
    expect(shelfVisual(47, null)).toEqual(shelfVisual(47, null))
    expect(shelfVisual(47, -8).width).toBe(48)
    expect(shelfVisual(47, 999999).width).toBe(60)
  })
})
