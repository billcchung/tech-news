export function filterItems(items, {category = 'All', tag = 'All', query = ''} = {}) {
  const normalizedQuery = query.trim().toLowerCase();
  return items.filter(item => {
    if (category !== 'All' && item.category !== category) return false;
    if (tag !== 'All' && !(item.tags || []).includes(tag)) return false;
    if (!normalizedQuery) return true;
    const searchable = [
      item.title,
      item.summary,
      item.source,
      item.category,
      ...(item.tags || []),
    ].join(' ').toLowerCase();
    return searchable.includes(normalizedQuery);
  });
}


export function categoryCounts(items) {
  const counts = new Map();
  for (const item of items) {
    counts.set(item.category, (counts.get(item.category) || 0) + 1);
  }
  return [
    {name: 'All', count: items.length},
    ...[...counts.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([name, count]) => ({name, count})),
  ];
}


export function availableTags(items) {
  const counts = new Map();
  for (const item of items) {
    for (const tag of item.tags || []) {
      counts.set(tag, (counts.get(tag) || 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, count]) => ({name, count}));
}


export function groupByDay(items) {
  const sorted = [...items].sort((left, right) => {
    const leftDate = left.published || left.first_seen || '';
    const rightDate = right.published || right.first_seen || '';
    return rightDate.localeCompare(leftDate);
  });
  const groups = [];
  for (const item of sorted) {
    const day = (item.published || item.first_seen || 'Undated').slice(0, 10);
    const current = groups.at(-1);
    if (!current || current.day !== day) {
      groups.push({day, items: [item]});
    } else {
      current.items.push(item);
    }
  }
  return groups;
}


export function archivePath(month) {
  if (!/^\d{4}-(?:0[1-9]|1[0-2])$/.test(month)) {
    throw new Error(`Invalid archive month: ${month}`);
  }
  return `archive/${month}.json`;
}


export async function loadDataset(path, previousItems, fetchJson = defaultFetchJson) {
  try {
    const payload = await fetchJson(path);
    if (!payload || !Array.isArray(payload.items)) {
      throw new Error('News data has no items array');
    }
    return {items: payload.items, payload, error: null};
  } catch (error) {
    return {
      items: previousItems,
      payload: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}


async function defaultFetchJson(path) {
  const separator = path.includes('?') ? '&' : '?';
  const response = await fetch(`${path}${separator}t=${Date.now()}`);
  if (!response.ok) throw new Error(`Request failed with HTTP ${response.status}`);
  return response.json();
}


function formatMonth(month) {
  const date = new Date(`${month}-01T00:00:00Z`);
  return date.toLocaleDateString(undefined, {month: 'long', year: 'numeric', timeZone: 'UTC'});
}


function formatDay(day) {
  if (day === 'Undated') return day;
  const date = new Date(`${day}T00:00:00Z`);
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
}


function categoryClass(category) {
  return `category-${category.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;
}


function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}


async function initialize() {
  const elements = {
    archive: document.getElementById('archive'),
    categories: document.getElementById('categories'),
    empty: document.getElementById('empty'),
    list: document.getElementById('list'),
    search: document.getElementById('search'),
    status: document.getElementById('status'),
    tags: document.getElementById('tags'),
  };
  const state = {
    activeCategory: 'All',
    activeTag: 'All',
    items: [],
    payload: null,
    query: '',
    selectedMonth: 'Current',
  };

  const render = () => {
    renderFilters(elements, state, render);
    const visible = filterItems(state.items, {
      category: state.activeCategory,
      tag: state.activeTag,
      query: state.query,
    });
    renderArticles(elements, visible, state, render);
  };

  elements.search.addEventListener('input', event => {
    state.query = event.target.value;
    render();
  });

  elements.archive.addEventListener('change', async event => {
    const month = event.target.value;
    const path = month === 'Current' ? 'news.json' : archivePath(month);
    elements.archive.disabled = true;
    elements.status.textContent = `Loading ${month === 'Current' ? 'current news' : formatMonth(month)}…`;
    const result = await loadDataset(path, state.items);
    elements.archive.disabled = false;
    if (result.error) {
      elements.status.textContent = `Could not load archive: ${result.error}`;
      return;
    }
    state.items = result.items;
    state.payload = result.payload;
    state.selectedMonth = month;
    state.activeCategory = 'All';
    state.activeTag = 'All';
    updateStatus(elements.status, state);
    render();
  });

  const current = await loadDataset('news.json', []);
  if (current.error) {
    elements.status.textContent = `Could not load news: ${current.error}`;
    return;
  }
  state.items = current.items;
  state.payload = current.payload;

  try {
    const manifest = await defaultFetchJson('archive/index.json');
    for (const entry of manifest.months || []) {
      if (!/^\d{4}-(?:0[1-9]|1[0-2])$/.test(entry.month)) continue;
      const option = document.createElement('option');
      option.value = entry.month;
      option.textContent = `${formatMonth(entry.month)} (${entry.count})`;
      elements.archive.appendChild(option);
    }
  } catch {
    const option = document.createElement('option');
    option.disabled = true;
    option.textContent = 'Archive unavailable';
    elements.archive.appendChild(option);
  }

  updateStatus(elements.status, state);
  render();
}


function updateStatus(element, state) {
  const updated = state.payload?.updated ? new Date(state.payload.updated).toLocaleString() : 'unknown';
  const unavailable = state.payload?.failed_sources?.length
    ? ` · unavailable: ${state.payload.failed_sources.join(', ')}`
    : '';
  const scope = state.selectedMonth === 'Current' ? 'Current feed' : formatMonth(state.selectedMonth);
  element.textContent = `${scope} · ${state.items.length} articles · updated ${updated}${unavailable}`;
}


function renderFilters(elements, state, render) {
  elements.categories.replaceChildren();
  for (const {name, count} of categoryCounts(state.items)) {
    const button = createElement('button', name === state.activeCategory ? 'filter active' : 'filter');
    button.type = 'button';
    button.textContent = `${name} ${count}`;
    button.addEventListener('click', () => {
      state.activeCategory = name;
      render();
    });
    elements.categories.appendChild(button);
  }

  elements.tags.replaceChildren();
  const allTags = createElement('button', state.activeTag === 'All' ? 'tag-filter active' : 'tag-filter', 'All tags');
  allTags.type = 'button';
  allTags.addEventListener('click', () => {
    state.activeTag = 'All';
    render();
  });
  elements.tags.appendChild(allTags);
  for (const {name, count} of availableTags(state.items)) {
    const button = createElement('button', name === state.activeTag ? 'tag-filter active' : 'tag-filter');
    button.type = 'button';
    button.textContent = `${name} ${count}`;
    button.addEventListener('click', () => {
      state.activeTag = name;
      render();
    });
    elements.tags.appendChild(button);
  }
}


function renderArticles(elements, items, state, render) {
  elements.list.replaceChildren();
  elements.empty.hidden = items.length > 0;
  for (const group of groupByDay(items)) {
    const section = createElement('section', 'day-group');
    section.appendChild(createElement('h2', 'day-heading', formatDay(group.day)));
    for (const item of group.items) {
      const article = createElement('article', 'item');
      const title = createElement('a', 'title', item.title);
      title.href = item.link;
      title.target = '_blank';
      title.rel = 'noopener noreferrer';
      article.appendChild(title);

      const meta = createElement('div', 'meta');
      meta.appendChild(createElement('span', `badge ${categoryClass(item.category)}`, item.category));
      meta.appendChild(createElement('span', 'source', item.source));
      if (item.published) {
        const time = createElement('time', '', new Date(item.published).toLocaleString());
        time.dateTime = item.published;
        meta.appendChild(time);
      }
      article.appendChild(meta);

      if (item.tags?.length) {
        const tags = createElement('div', 'article-tags');
        for (const tag of item.tags) {
          const button = createElement('button', 'article-tag', tag);
          button.type = 'button';
          button.addEventListener('click', () => {
            state.activeTag = tag;
            render();
            window.scrollTo({top: 0, behavior: 'smooth'});
          });
          tags.appendChild(button);
        }
        article.appendChild(tags);
      }

      if (item.summary) {
        const excerpt = createElement('div', 'excerpt');
        excerpt.appendChild(createElement('span', 'excerpt-label', 'Publisher excerpt'));
        excerpt.appendChild(createElement('p', '', item.summary));
        article.appendChild(excerpt);
      }
      section.appendChild(article);
    }
    elements.list.appendChild(section);
  }
}


if (typeof document !== 'undefined') {
  initialize().catch(error => {
    const status = document.getElementById('status');
    if (status) status.textContent = `Could not start the application: ${error.message}`;
  });
}
