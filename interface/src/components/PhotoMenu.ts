interface CollectionRef {
  name: string;
  title: string;
}

let menu: HTMLDivElement | null = null;
let submenu: HTMLDivElement | null = null;
let activeCard: HTMLElement | null = null;
let activeAnchor: HTMLElement | null = null;

let openTimer: number | null = null;
let closeTimer: number | null = null;

let collectionsCache: CollectionRef[] | null = null;
let collectionsPromise: Promise<CollectionRef[]> | null = null;

const OPEN_DELAY = 120;
const CLOSE_DELAY = 120;

// ---------- data ----------

function loadCollections(): Promise<CollectionRef[]> {
  if (collectionsCache) return Promise.resolve(collectionsCache);
  if (!collectionsPromise) {
    collectionsPromise = fetch('/api/collections')
      .then((r) => r.json())
      .then((data: CollectionRef[]) => {
        collectionsCache = data;
        return data;
      })
      .catch(() => {
        collectionsPromise = null;
        return [];
      });
  }
  return collectionsPromise;
}

function photoCollections(card: HTMLElement): string[] {
  return (card.dataset.photoCollections ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

// ---------- escaping ----------

function escapeAttr(s: string): string {
  return s.replace(/"/g, '&quot;');
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ---------- render ----------

function renderMenu(card: HTMLElement): string {
  const inCollection = card.dataset.collectionContext;
  const inSet = new Set(photoCollections(card));
  const available = (collectionsCache ?? []).filter((c) => !inSet.has(c.name));

  const items: string[] = [];

  if (collectionsCache === null) {
    items.push(
      `<button class="pm-item pm-disabled" disabled>Add to collection<span class="pm-loading">…</span></button>`,
    );
  } else if (available.length > 0) {
    items.push(
      `<button class="pm-item pm-has-submenu" data-pm-action="show-add">Add to collection<span class="pm-arrow">›</span></button>`,
    );
  }

  if (inCollection && card.dataset.isCover !== 'true') {
    items.push(
      `<button class="pm-item" data-pm-action="set-cover">Set as cover</button>`,
    );
  }

  if (inCollection) {
    items.push(
      `<button class="pm-item" data-pm-action="remove-from-collection">Remove from collection</button>`,
    );
  }

  if (items.length > 0) items.push(`<div class="pm-sep"></div>`);

  items.push(
    `<button class="pm-item pm-danger" data-pm-action="delete">Delete from portfolio…</button>`,
  );

  return items.join('');
}

function renderSubmenu(card: HTMLElement): string {
  const inSet = new Set(photoCollections(card));
  const available = (collectionsCache ?? []).filter((c) => !inSet.has(c.name));

  if (available.length === 0) {
    return `<div class="pm-empty">No other collections.</div>`;
  }

  return available
    .map(
      (c) =>
        `<button class="pm-item" data-pm-action="add-to" data-collection="${escapeAttr(c.name)}">${escapeHtml(c.title || c.name)}</button>`,
    )
    .join('');
}

// ---------- timers ----------

function clearOpenTimer(): void {
  if (openTimer !== null) {
    clearTimeout(openTimer);
    openTimer = null;
  }
}

function clearCloseTimer(): void {
  if (closeTimer !== null) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function scheduleCloseSubmenu(): void {
  clearCloseTimer();
  closeTimer = window.setTimeout(() => {
    closeSubmenu();
    closeTimer = null;
  }, CLOSE_DELAY);
}

// ---------- DOM construction ----------

function build(): void {
  menu = document.createElement('div');
  menu.className = 'photo-menu';
  document.body.appendChild(menu);

  submenu = document.createElement('div');
  submenu.className = 'photo-submenu';
  document.body.appendChild(submenu);

  menu.addEventListener('click', onMenuClick);
  menu.addEventListener('mouseover', onMenuOver);
  menu.addEventListener('mouseleave', onMenuLeave);

  submenu.addEventListener('click', onSubmenuClick);
  submenu.addEventListener('mouseenter', clearCloseTimer);
  submenu.addEventListener('mouseleave', scheduleCloseSubmenu);
}

// ---------- positioning ----------

function placeMenu(x: number, y: number): void {
  if (!menu) return;
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
  requestAnimationFrame(() => {
    if (!menu) return;
    const r = menu.getBoundingClientRect();
    if (r.right > window.innerWidth - 8) {
      menu.style.left = `${Math.max(8, x - r.width)}px`;
    }
    if (r.bottom > window.innerHeight - 8) {
      menu.style.top = `${Math.max(8, y - r.height)}px`;
    }
  });
}

function placeSubmenu(anchor: HTMLElement): void {
  if (!submenu) return;
  const a = anchor.getBoundingClientRect();
  // Render off-screen first so we can measure
  submenu.style.visibility = 'hidden';
  submenu.style.left = '0px';
  submenu.style.top = '0px';
  requestAnimationFrame(() => {
    if (!submenu) return;
    const sr = submenu.getBoundingClientRect();
    let left = a.right + 2;
    let top = a.top - 4;
    if (left + sr.width > window.innerWidth - 8) {
      left = Math.max(8, a.left - sr.width - 2);
    }
    if (top + sr.height > window.innerHeight - 8) {
      top = Math.max(8, window.innerHeight - sr.height - 8);
    }
    submenu.style.left = `${left}px`;
    submenu.style.top = `${top}px`;
    submenu.style.visibility = '';
  });
}

// ---------- open / close ----------

function openMenu(card: HTMLElement, x: number, y: number): void {
  if (!menu) build();
  closeSubmenu();
  if (activeCard && activeCard !== card) activeCard.classList.remove('menu-open');
  activeCard = card;
  card.classList.add('menu-open');
  menu!.innerHTML = renderMenu(card);
  menu!.classList.add('open');
  placeMenu(x, y);

  if (collectionsCache === null) {
    void loadCollections().then(() => {
      if (activeCard === card && menu?.classList.contains('open')) {
        menu.innerHTML = renderMenu(card);
      }
    });
  }
}

function openSubmenu(anchor: HTMLElement, card: HTMLElement): void {
  if (!submenu) return;
  clearOpenTimer();
  clearCloseTimer();
  if (activeAnchor === anchor && submenu.classList.contains('open')) return;
  activeAnchor?.classList.remove('pm-item-active');
  activeAnchor = anchor;
  anchor.classList.add('pm-item-active');
  submenu.innerHTML = renderSubmenu(card);
  submenu.classList.add('open');
  placeSubmenu(anchor);
}

function closeSubmenu(): void {
  clearOpenTimer();
  clearCloseTimer();
  if (submenu) submenu.classList.remove('open');
  activeAnchor?.classList.remove('pm-item-active');
  activeAnchor = null;
}

function closeAll(): void {
  closeSubmenu();
  if (menu) menu.classList.remove('open');
  activeCard?.classList.remove('menu-open');
  activeCard = null;
}

// ---------- event handlers ----------

function onMenuClick(e: MouseEvent): void {
  e.stopPropagation();
  const item = (e.target as HTMLElement).closest<HTMLElement>('[data-pm-action]');
  if (!item || !activeCard) return;
  const action = item.dataset.pmAction!;
  const card = activeCard;

  if (action === 'show-add') {
    openSubmenu(item, card);
    return;
  }
  closeAll();
  void performAction(action, card);
}

function onMenuOver(e: MouseEvent): void {
  const item = (e.target as HTMLElement).closest<HTMLElement>('[data-pm-action]');
  if (!item || !activeCard) return;
  const card = activeCard;
  const action = item.dataset.pmAction;

  clearCloseTimer();

  if (action === 'show-add') {
    if (activeAnchor === item) return;
    clearOpenTimer();
    openTimer = window.setTimeout(() => {
      openTimer = null;
      if (activeCard === card) openSubmenu(item, card);
    }, OPEN_DELAY);
  } else {
    // Hovering an item that has no submenu: cancel pending open, retreat submenu.
    clearOpenTimer();
    if (submenu?.classList.contains('open')) scheduleCloseSubmenu();
  }
}

function onMenuLeave(e: MouseEvent): void {
  clearOpenTimer();
  const related = e.relatedTarget as HTMLElement | null;
  if (related && submenu?.contains(related)) return; // moving onto submenu — keep open
  scheduleCloseSubmenu();
}

function onSubmenuClick(e: MouseEvent): void {
  e.stopPropagation();
  const item = (e.target as HTMLElement).closest<HTMLElement>('[data-pm-action="add-to"]');
  if (!item || !activeCard) return;
  const target = item.dataset.collection;
  if (!target) return;
  const card = activeCard;
  closeAll();
  void addToCollection(card, target);
}

// ---------- mutations ----------

async function performAction(action: string, card: HTMLElement): Promise<void> {
  const filename = card.dataset.photoFilename ?? '';
  const photoPath = card.dataset.photoPath ?? '';
  const collection = card.dataset.collectionContext;

  if (action === 'delete') {
    const ok = confirm(
      `Delete "${filename}" from the entire portfolio?\n\nThis cascades to:\n  • photos/ source jpg\n  • data/photos/ metadata\n  • r2/small + r2/large variants\n  • all collection references`,
    );
    if (!ok) return;
    const res = await fetch('/api/photos/delete', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ path: photoPath }),
    });
    if (res.ok) card.remove();
    else alert(`Delete failed:\n\n${await res.text()}`);
    return;
  }

  if (action === 'remove-from-collection' && collection) {
    const res = await fetch(`/api/collections/${collection}/remove-photo`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ path: photoPath }),
    });
    if (res.ok) card.remove();
    else alert(`Remove failed:\n\n${await res.text()}`);
    return;
  }

  if (action === 'set-cover' && collection) {
    const res = await fetch(`/api/collections/${collection}/update`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ cover_path: photoPath }),
    });
    if (!res.ok) {
      alert(`Set cover failed:\n\n${await res.text()}`);
      return;
    }
    document
      .querySelectorAll<HTMLElement>('.card[data-is-cover="true"]')
      .forEach((c) => c.removeAttribute('data-is-cover'));
    card.setAttribute('data-is-cover', 'true');
  }
}

async function addToCollection(card: HTMLElement, collectionName: string): Promise<void> {
  const photoPath = card.dataset.photoPath ?? '';
  const res = await fetch(`/api/collections/${collectionName}/add-photo`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ path: photoPath }),
  });
  if (!res.ok) {
    alert(`Add failed:\n\n${await res.text()}`);
    return;
  }

  const current = photoCollections(card);
  if (!current.includes(collectionName)) {
    current.push(collectionName);
    card.dataset.photoCollections = current.join(',');
  }
  appendChip(card, collectionName);
}

function appendChip(card: HTMLElement, collectionName: string): void {
  const label = collectionsCache?.find((c) => c.name === collectionName)?.title || collectionName;
  let chips = card.querySelector<HTMLDivElement>('.chips');
  const template = card.querySelector<HTMLElement>('.chip');

  if (!chips) {
    chips = document.createElement('div');
    chips.className = 'chips';
    const meta = card.querySelector<HTMLElement>('.meta');
    const scopeAttr = meta ? findAstroCid(meta.attributes) : null;
    if (scopeAttr) chips.setAttribute(scopeAttr, '');
    meta?.appendChild(chips);
  }

  const chip = document.createElement('span');
  chip.className = 'chip';
  if (template) {
    const scope = findAstroCid(template.attributes);
    if (scope) chip.setAttribute(scope, '');
  }
  chip.textContent = label;
  chips.appendChild(chip);
}

function findAstroCid(attrs: NamedNodeMap): string | null {
  for (const a of Array.from(attrs)) {
    if (a.name.startsWith('data-astro-cid-')) return a.name;
  }
  return null;
}

// ---------- styles ----------

const STYLES = `
.photo-menu, .photo-submenu {
  position: fixed;
  display: none;
  flex-direction: column;
  min-width: 220px;
  padding: 4px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow);
  z-index: 1100;
  animation: pm-in 80ms ease-out;
}
.photo-submenu { min-width: 180px; }
.photo-menu.open, .photo-submenu.open { display: flex; }
@keyframes pm-in {
  from { opacity: 0; transform: translateY(-2px); }
  to   { opacity: 1; transform: translateY(0); }
}
.pm-item {
  all: unset;
  font-size: 13px;
  padding: 7px 10px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pm-item:hover:not(.pm-disabled),
.pm-item.pm-item-active {
  background: var(--surface);
}
.pm-item.pm-danger { color: var(--danger); }
.pm-item.pm-disabled { cursor: default; color: var(--text-faint); }
.pm-arrow {
  margin-left: auto;
  color: var(--text-faint);
  font-size: 14px;
  line-height: 1;
}
.pm-loading {
  margin-left: auto;
  color: var(--text-faint);
  font-size: 11px;
}
.pm-sep {
  height: 1px;
  background: var(--border);
  margin: 4px 6px;
}
.pm-empty {
  padding: 8px 10px;
  font-size: 12px;
  color: var(--text-faint);
  font-style: italic;
}
.card.menu-open .thumb { border-color: var(--border-strong); }
`;

function injectStyles(): void {
  if (document.getElementById('photo-menu-styles')) return;
  const s = document.createElement('style');
  s.id = 'photo-menu-styles';
  s.textContent = STYLES;
  document.head.appendChild(s);
}

// ---------- public ----------

export function initPhotoMenu(): void {
  injectStyles();
  void loadCollections();

  document.addEventListener('click', (e) => {
    const t = e.target as HTMLElement;
    const trigger = t.closest<HTMLElement>('[data-action="open-menu"]');
    if (trigger) {
      e.preventDefault();
      e.stopPropagation();
      const card = trigger.closest<HTMLElement>('.card');
      if (!card) return;
      const r = trigger.getBoundingClientRect();
      openMenu(card, r.left, r.bottom + 4);
      return;
    }
    const inMenu = menu?.contains(t);
    const inSubmenu = submenu?.contains(t);
    if (menu?.classList.contains('open') && !inMenu && !inSubmenu) {
      closeAll();
    }
  });

  document.addEventListener('contextmenu', (e) => {
    const card = (e.target as HTMLElement).closest<HTMLElement>('.card');
    if (!card) return;
    e.preventDefault();
    openMenu(card, e.clientX, e.clientY);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (submenu?.classList.contains('open')) {
      closeSubmenu();
    } else if (menu?.classList.contains('open')) {
      closeAll();
    }
  });

  window.addEventListener('scroll', () => closeAll(), true);
  window.addEventListener('resize', () => closeAll());
}
