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
  function locate(issue, source, current) {
    const chars = Array.from(source);
    const oldStart = chars.slice(0, issue.start).join('').length;
    const oldEnd = chars.slice(0, issue.end).join('').length;
    if (source.slice(oldStart, oldEnd) !== issue.quote) return null;
    if (source === current) return {start: oldStart, end: oldEnd, basis: 'same-draft'};
    const paragraph = paragraphs(source)[issue.paragraph - 1];
    if (!paragraph) return null;
    const first = current.indexOf(paragraph.text);
    if (first < 0 || current.indexOf(paragraph.text, first + 1) >= 0) return null;
    const start = first + oldStart - paragraph.start;
    const end = start + issue.quote.length;
    if (current.slice(start, end) !== issue.quote) return null;
    return {start, end, basis: 'unchanged-paragraph'};
  }
  const api = {locate, paragraphs};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.WorkshopAnchors = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
