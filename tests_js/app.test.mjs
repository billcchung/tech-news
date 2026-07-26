import assert from 'node:assert/strict';
import test from 'node:test';

import {
  archivePath,
  availableTags,
  categoryCounts,
  filterItems,
  groupByDay,
  loadDataset,
} from '../site/app.mjs';


const items = [
  {
    id: 'security-browser',
    title: 'Browser security update',
    summary: 'A privacy fix',
    source: 'Mozilla Hacks',
    category: 'Security & Privacy',
    tags: ['privacy', 'security', 'web'],
    published: '2026-07-25T10:00:00+00:00',
    first_seen: '2026-07-25T12:00:00+00:00',
  },
  {
    id: 'cloud-database',
    title: 'Cloud database release',
    summary: 'New SQL support',
    source: 'Cloud Example',
    category: 'Cloud & Infrastructure',
    tags: ['cloud', 'databases'],
    published: '2026-07-24T10:00:00+00:00',
    first_seen: '2026-07-24T12:00:00+00:00',
  },
];


test('combines category tag and text filters', () => {
  const result = filterItems(items, {
    category: 'Security & Privacy',
    tag: 'security',
    query: 'browser',
  });

  assert.deepEqual(result.map(item => item.id), ['security-browser']);
});


test('search includes source summary and tags', () => {
  assert.equal(filterItems(items, {category: 'All', tag: 'All', query: 'mozilla'}).length, 1);
  assert.equal(filterItems(items, {category: 'All', tag: 'All', query: 'sql'}).length, 1);
  assert.equal(filterItems(items, {category: 'All', tag: 'All', query: 'databases'}).length, 1);
});


test('category and tag counts are deterministic', () => {
  assert.deepEqual(categoryCounts(items), [
    {name: 'All', count: 2},
    {name: 'Cloud & Infrastructure', count: 1},
    {name: 'Security & Privacy', count: 1},
  ]);
  assert.deepEqual(availableTags(items), [
    {name: 'cloud', count: 1},
    {name: 'databases', count: 1},
    {name: 'privacy', count: 1},
    {name: 'security', count: 1},
    {name: 'web', count: 1},
  ]);
});


test('groups articles by publication day newest first', () => {
  assert.deepEqual(
    groupByDay([...items].reverse()).map(group => [group.day, group.items[0].id]),
    [
      ['2026-07-25', 'security-browser'],
      ['2026-07-24', 'cloud-database'],
    ],
  );
});


test('validates archive month paths', () => {
  assert.equal(archivePath('2026-07'), 'archive/2026-07.json');
  assert.throws(() => archivePath('../news'), /Invalid archive month/);
  assert.throws(() => archivePath('2026-13'), /Invalid archive month/);
});


test('preserves current items when archive loading fails', async () => {
  const result = await loadDataset(
    'archive/2026-07.json',
    items,
    async () => {
      throw new Error('offline');
    },
  );

  assert.equal(result.items, items);
  assert.match(result.error, /offline/);
});
