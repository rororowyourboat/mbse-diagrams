import test from 'node:test';
import assert from 'node:assert/strict';
import { resolvedModelRef } from '../src/model-ref.js';

test('resolves source aliases to a cross-view key', () => {
  const diagram = { sources: [{ id: 'source-1', uri: 'structure.sysml', revision: 'sha256:abc' }] };
  assert.equal(resolvedModelRef(diagram, { source: 'source-1', element: 'span:4:4:9:20' }), 'structure.sysml#span:4:4:9:20');
});

test('keeps the element reference when the source alias is unavailable', () => {
  const diagram = { sources: [] };
  assert.equal(resolvedModelRef(diagram, { source: 'missing', element: 'element-42' }), 'element-42');
});

test('unbound presentations have no cross-view key', () => {
  assert.equal(resolvedModelRef({ sources: [] }, null), null);
});
