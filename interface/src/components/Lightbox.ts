interface PhotoRef {
  id: string;
  filename: string;
}

let overlay: HTMLDivElement | null = null;
let img: HTMLImageElement | null = null;
let caption: HTMLDivElement | null = null;
let photos: PhotoRef[] = [];
let index = 0;

function build(): HTMLDivElement {
  const el = document.createElement('div');
  el.className = 'lightbox';
  el.innerHTML = `
    <button class="lb-close" data-lb="close" aria-label="Close">
      <svg viewBox="0 0 16 16" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
    </button>
    <button class="lb-prev" data-lb="prev" aria-label="Previous">
      <svg viewBox="0 0 16 16" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3L5 8l5 5"/></svg>
    </button>
    <button class="lb-next" data-lb="next" aria-label="Next">
      <svg viewBox="0 0 16 16" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3l5 5-5 5"/></svg>
    </button>
    <div class="lb-stage">
      <img class="lb-img" alt="" />
    </div>
    <div class="lb-caption"></div>
  `;
  document.body.appendChild(el);

  el.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const action = target.closest('[data-lb]')?.getAttribute('data-lb');
    if (action === 'close' || target === el || target.classList.contains('lb-stage')) {
      close();
    } else if (action === 'prev') {
      step(-1);
    } else if (action === 'next') {
      step(1);
    }
  });

  img = el.querySelector('.lb-img');
  caption = el.querySelector('.lb-caption');
  return el;
}

function gather(): PhotoRef[] {
  return Array.from(document.querySelectorAll<HTMLElement>('.card')).map((card) => ({
    id: card.dataset.photoId ?? '',
    filename: card.dataset.photoFilename ?? '',
  }));
}

function render(): void {
  if (!img || !caption) return;
  const p = photos[index];
  if (!p) return;
  img.src = `/api/img/large/${p.id}.webp`;
  img.alt = p.filename;
  caption.textContent = `${p.filename}  ·  ${index + 1} / ${photos.length}`;
}

function open(startId: string): void {
  if (!overlay) overlay = build();
  photos = gather();
  const i = photos.findIndex((p) => p.id === startId);
  if (i < 0) return;
  index = i;
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  render();
}

function close(): void {
  if (!overlay) return;
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}

function step(delta: number): void {
  if (photos.length === 0) return;
  index = (index + delta + photos.length) % photos.length;
  render();
}

function isOpen(): boolean {
  return overlay?.classList.contains('open') ?? false;
}

const STYLES = `
.lightbox {
  position: fixed; inset: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  z-index: 1000;
  display: none;
  align-items: center; justify-content: center;
  animation: lb-in 120ms ease-out;
}
.lightbox.open { display: flex; }
@keyframes lb-in { from { opacity: 0; } to { opacity: 1; } }
.lb-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 92vw;
  height: 86vh;
}
.lb-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  background: var(--surface);
}
.lb-caption {
  position: absolute;
  bottom: 22px; left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}
.lb-close, .lb-prev, .lb-next {
  position: absolute;
  background: transparent;
  border: none;
  color: var(--text);
  cursor: pointer;
  padding: 10px;
  border-radius: var(--radius);
  opacity: 0.55;
  transition: opacity var(--transition), background var(--transition);
  display: flex; align-items: center; justify-content: center;
}
.lb-close:hover, .lb-prev:hover, .lb-next:hover {
  opacity: 1;
  background: var(--surface);
}
.lb-close { top: 18px; right: 22px; }
.lb-prev  { left: 18px;  top: 50%; transform: translateY(-50%); }
.lb-next  { right: 18px; top: 50%; transform: translateY(-50%); }
`;

function injectStyles(): void {
  if (document.getElementById('lightbox-styles')) return;
  const s = document.createElement('style');
  s.id = 'lightbox-styles';
  s.textContent = STYLES;
  document.head.appendChild(s);
}

export function initLightbox(): void {
  injectStyles();

  document.addEventListener('click', (e) => {
    const trigger = (e.target as HTMLElement).closest('[data-action="open-lightbox"]');
    if (!trigger) return;
    const card = trigger.closest<HTMLElement>('.card');
    if (!card) return;
    open(card.dataset.photoId ?? '');
  });

  document.addEventListener('keydown', (e) => {
    if (!isOpen()) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') step(-1);
    else if (e.key === 'ArrowRight') step(1);
  });
}
