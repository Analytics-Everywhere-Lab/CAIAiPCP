// Anchoring feedback notes to text in the rendered care plan.
//
// A note stores character offsets into the text of one plan section, plus the
// quoted text. The plan's DOM is re-created whenever the document re-mounts
// (switching tabs, collapsing a section), so live Range objects cannot be kept;
// ranges are rebuilt from the offsets, and from the quote if the offsets drift.
// Highlights are drawn in an overlay instead of editing the rendered markdown.

const normalize = (text) => (text || '').replace(/\s+/g, ' ').trim()

export function offsetsFromRange(container, range) {
  const before = document.createRange()
  before.selectNodeContents(container)
  before.setEnd(range.startContainer, range.startOffset)
  const start = before.toString().length
  return { start, end: start + range.toString().length }
}

export function rangeFromOffsets(container, start, end) {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
  const range = document.createRange()
  let position = 0
  let startSet = false
  let node = walker.nextNode()
  while (node) {
    const length = node.data.length
    if (!startSet && start <= position + length) {
      range.setStart(node, Math.max(0, start - position))
      startSet = true
    }
    if (startSet && end <= position + length) {
      range.setEnd(node, Math.max(0, end - position))
      return range
    }
    position += length
    node = walker.nextNode()
  }
  return null
}

// Rebuild a note's range in the current DOM; null when the text is gone.
export function resolveRange(container, note) {
  if (!container || note.start == null) return null
  const direct = rangeFromOffsets(container, note.start, note.end)
  if (direct && normalize(direct.toString()) === normalize(note.quote)) return direct
  const index = (container.textContent || '').indexOf(note.quote || '\u0000')
  return index >= 0 ? rangeFromOffsets(container, index, index + note.quote.length) : null
}

// The selection inside one plan section, as a note anchor; null otherwise.
export function selectionAnchor(root) {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return null
  const range = selection.getRangeAt(0)
  const quote = range.toString()
  if (normalize(quote).length < 2) return null
  const element = (node) => (node.nodeType === 1 ? node : node.parentElement)
  const container = element(range.startContainer)?.closest('[data-anchor-root]')
  if (!container || !root?.contains(container) || !container.contains(range.endContainer)) return null
  const { start, end } = offsetsFromRange(container, range)
  return { sectionId: container.dataset.anchorRoot, quote: quote.slice(0, 600), start, end, range }
}

// Client rects of a range relative to a positioned host element, merged per line.
export function rectsWithin(range, host) {
  const base = host.getBoundingClientRect()
  const lines = []
  for (const rect of Array.from(range.getClientRects())) {
    if (rect.width < 1 || rect.height < 1) continue
    const box = { top: rect.top - base.top, left: rect.left - base.left, width: rect.width, height: rect.height }
    const line = lines.find(l => Math.abs(l.top - box.top) < 3 && box.left <= l.left + l.width + 2)
    if (line) {
      const right = Math.max(line.left + line.width, box.left + box.width)
      line.left = Math.min(line.left, box.left)
      line.width = right - line.left
      line.height = Math.max(line.height, box.height)
    } else {
      lines.push(box)
    }
  }
  return lines
}

// Stack note cards beside their anchors without overlapping (Docs-style margin).
export function layoutCards(items, heights, gap = 10) {
  const positions = {}
  let bottom = -Infinity
  for (const item of [...items].sort((a, b) => a.top - b.top || a.order - b.order)) {
    const top = Math.max(item.top, bottom + gap)
    positions[item.id] = top
    bottom = top + (heights[item.id] || 96)
  }
  return positions
}
