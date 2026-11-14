// Shows a draft notice at the top of every page until edition 0.1 is released.
// Remove this file (and its entry in book.toml) at release.
(function () {
  var main = document.querySelector("main");
  if (!main) return;
  var note = document.createElement("div");
  note.className = "draft-banner";
  note.textContent = "Draft of edition 0.1. Under review and not yet released; the text may change.";
  main.insertBefore(note, main.firstChild);
})();
