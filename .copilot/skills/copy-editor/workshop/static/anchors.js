/* Conservative navigation to the author's existing text. Never fuzzy-match a changed quote. */
(function (root) {
  'use strict';
  function paragraphs(text) {
    const result = []; let start = 0;
    for (const match of text.matchAll(/\n[ \t]*\n(?:[ \t]*\n)*/g)) {
      const part = text.slice(start, match.index);
      if (part.trim()) result.push({start, text: part});
      start = match.index + match[0].length;
    }
    if (text.slice(start).trim()) result.push({start, text: text.slice(start)});
    return result;
  }
  let prepared = {source: null};
  // Caches per-source offsets so live highlighting does not reparse the reviewed text on each keystroke.
  function prepare(source) {
    if (prepared.source !== source) {
      const prefix = [0];
      for (const ch of source) prefix.push(prefix[prefix.length - 1] + ch.length);
      prepared = {source, prefix, paragraphs: paragraphs(source)};
    }
    return prepared;
  }
  function locateAll(issues, source, current) {
    const {prefix, paragraphs: sourceParagraphs} = prepare(source);
    const clamp = (point) => prefix[Math.max(0, Math.min(point, prefix.length - 1))];
    const paragraphAt = new Map();
    const ranges = [];
    for (const issue of issues) {
      const oldStart = clamp(issue.start), oldEnd = clamp(issue.end);
      if (source.slice(oldStart, oldEnd) !== issue.quote) continue;
      if (source === current) { ranges.push({id: issue.id, start: oldStart, end: oldEnd, basis: 'same-draft'}); continue; }
      const paragraph = sourceParagraphs[issue.paragraph - 1];
      if (!paragraph) continue;
      if (!paragraphAt.has(issue.paragraph)) {
        const first = current.indexOf(paragraph.text);
        paragraphAt.set(issue.paragraph, first < 0 || current.indexOf(paragraph.text, first + 1) >= 0 ? -1 : first);
      }
      const at = paragraphAt.get(issue.paragraph);
      if (at < 0) continue;
      const start = at + oldStart - paragraph.start;
      const end = start + issue.quote.length;
      if (current.slice(start, end) !== issue.quote) continue;
      ranges.push({id: issue.id, start, end, basis: 'unchanged-paragraph'});
    }
    return ranges;
  }
  function locate(issue, source, current) {
    const [range] = locateAll([issue], source, current);
    return range ? {start: range.start, end: range.end, basis: range.basis} : null;
  }
  const api = {locate, locateAll, paragraphs};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.WorkshopAnchors = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
