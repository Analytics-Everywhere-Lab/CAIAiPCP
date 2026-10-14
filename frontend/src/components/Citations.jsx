// Citations are stored as [REF-n] (what the model writes and the server checks) and shown
// IEEE-style: [n], linked to the matching entry of a reference list.

const CITATION = /\[REF-(\d+)\]/g

// Adjacent citations read "[1], [2]".
function separate(text) {
  return (text || '').replace(/(\[REF-\d+\])(?=\[REF-\d+\])/g, '$1, ')
}

// Plain text with [n] citations, for tooltips, titles and editing.
export function ieeeText(text) {
  return separate(text).replace(CITATION, '[$1]')
}

// Back from [n] to [REF-n] when an edited text is saved; only numbers of known sources are citations.
export function fromIeee(text, refIds) {
  return (text || '').replace(/\[(\d+)\]/g, (match, n) => (refIds?.has(Number(n)) ? `[REF-${n}]` : match))
}

// Markdown with each known citation as a link to its reference entry, and others as plain [n].
export function citationMarkdown(markdown, refIds, anchor = 'ref-') {
  return separate(markdown).replace(CITATION, (match, n) =>
    refIds?.has(Number(n)) ? `[\\[${n}\\]](#${anchor}${n})` : `[${n}]`)
}

// Clip text to max characters without cutting a citation in half.
export function clipCited(text, max) {
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  if (clean.length <= max) return clean
  let cut = clean.slice(0, max - 1)
  const open = cut.lastIndexOf('[')
  if (open >= 0 && cut.indexOf(']', open) < 0) cut = cut.slice(0, open)
  return cut.trimEnd() + '…'
}

// Text with [n] citation links. onCite(n, event) replaces the default jump to the anchor.
export function CitedText({ text, refIds, anchor = 'ref-', onCite }) {
  const source = separate(text)
  const parts = []
  let last = 0
  for (const match of source.matchAll(CITATION)) {
    if (match.index > last) parts.push(source.slice(last, match.index))
    const n = Number(match[1])
    parts.push(refIds?.has(n) ? (
      <a key={`${match.index}-${n}`} className="cite" href={`#${anchor}${n}`}
        onClick={onCite ? (event) => onCite(n, event) : undefined}>[{n}]</a>
    ) : `[${n}]`)
    last = match.index + match[0].length
  }
  if (last < source.length) parts.push(source.slice(last))
  return <>{parts}</>
}

// One reference list entry: [n], evidence type, citation, and its DOI or PMID as the link to the source.
export function ReferenceItem({ reference: ref, anchor = 'ref-' }) {
  const ident = ref.doi ? `doi:${ref.doi}` : ref.pmid ? `PMID: ${ref.pmid}` : ''
  const citation = ref.citation || ref.title || ''
  const text = ident && citation.endsWith(ident) ? citation.slice(0, -ident.length).trimEnd() : citation
  return (
    <li id={`${anchor}${ref.id}`}>
      <span className="ref-id">[{ref.id}]</span>
      {ref.kind && <span className="ref-kind">{ref.kind}</span>}
      <span className="ref-citation">{text}</span>
      {ref.url && (
        <> <a className="ref-link" href={ref.url} target="_blank" rel="noopener noreferrer">{ident || 'View source'}</a></>
      )}
    </li>
  )
}
