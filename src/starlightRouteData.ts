import type { APIContext } from 'astro';

// Sidebar config labels are single-set (English); localize them for the
// root zh-CN locale before any component (desktop Sidebar, mobile nav) reads
// `locals.starlightRoute.sidebar`. This runs on Starlight's klona'd copy of
// the route data, so mutating it is safe.

const LABELS: Record<string, string> = {
  Overview: '总览',
  Changelogs: '更新日志',
  Home: '首页',
  'Latest Preview': '最新预览版',
  'Latest Public': '最新公开版',
  'Version List': '版本列表',
};

export function onRequest(context: APIContext, next: () => Promise<void>) {
  const route = (context.locals as { starlightRoute?: { lang: string; sidebar: unknown[] } })
    .starlightRoute;
  if (route?.lang === 'zh-CN' && Array.isArray(route.sidebar)) {
    const walk = (entries: { label?: string; entries?: unknown[] }[]) => {
      for (const item of entries) {
        if (typeof item.label === 'string') item.label = LABELS[item.label] ?? item.label;
        if (Array.isArray(item.entries)) walk(item.entries as never);
      }
    };
    walk(route.sidebar as never);
  }
  return next();
}
