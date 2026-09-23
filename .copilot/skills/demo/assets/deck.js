window.demonstrationDeck = new Reveal({
  disableLayout: true,
  hash: true,
  controls: true,
  controlsTutorial: false,
  progress: true,
  slideNumber: 'c/t',
  center: false,
  transition: 'none',
  history: false,
  help: false,
});
window.demonstrationDeck.initialize();
window.demonstrationDeck.on('slidechanged', () => {
  for (const video of document.querySelectorAll('section:not(.present) video')) video.pause();
  window.demonstrationDeck.getCurrentSlide().scrollTop = 0;
});
for (const video of document.querySelectorAll('video')) {
  const showError = () => { video.nextElementSibling.hidden = false; };
  video.addEventListener('error', showError);
  if (video.error) showError();
}
