export function resolvedModelRef(diagram, ref) {
  if (!ref) return null;
  const source = diagram.sources.find(item => item.id === ref.source);
  return source ? `${source.uri}#${ref.element}` : ref.element;
}
