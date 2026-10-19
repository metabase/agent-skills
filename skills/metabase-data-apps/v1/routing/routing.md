# Add routing to a data app

A data app has no router library. Three primitives from `@metabase/embedding-sdk-react/data-app` make up the whole routing surface:

| API | Purpose |
|---|---|
| `<DataAppRouter>` | Wraps the app once. It takes no `basename`: the link and the hook detect the iframe's prefix (`/embed/apps/<slug>`) in Metabase, and use none in the dev preview. |
| `<DataAppLink to="/customers/42">` | An internal link. It renders a real `<a href>` and passes other anchor props through. Modifier and middle clicks go to the browser, but a new tab works only in the dev preview: in Metabase, the link points at the iframe's own URL, which shows "This data app can’t be opened directly." |
| `useDataAppLocation()` | Returns `{ pathname, navigate }`. Match `pathname` by equality, `startsWith`, or a regex, and call `navigate(to)` to navigate from code. |

- Never add `react-router-dom` or any other router, and never use `<BrowserRouter>` or `<HashRouter>`. A router library calls `history.pushState`, which the sandbox blocks, so navigating throws.
- Never call `history.pushState` yourself, and never read or write the parent page's URL. Both are blocked by design.
- Routing needs no change to `vite.config.ts`, because `dataAppConfig()` already externalizes `/data-app`. Edit `src/App.tsx` and add page components.
- No app yet? Scaffold one with `setup/setup.md` first.

## Wrap `App.tsx`

```tsx
import {
  DataAppLink,
  DataAppRouter,
  useDataAppLocation,
} from "@metabase/embedding-sdk-react/data-app";

import { CustomerDetail } from "./pages/CustomerDetail";
import { Customers } from "./pages/Customers";
import { Overview } from "./pages/Overview";

const TABS = [
  { path: "/", label: "Overview", render: () => <Overview /> },
  { path: "/customers", label: "Customers", render: () => <Customers /> },
];

// `/` and any unknown path resolve to the first tab, never to a blank page
function activeTab(pathname: string) {
  return (
    TABS.find((tab) => tab.path !== "/" && pathname.startsWith(tab.path)) ??
    TABS[0]
  );
}

// there is no useParams: match the path yourself
function useCustomerIdFromPath(): number | null {
  const { pathname } = useDataAppLocation();
  const match = pathname.match(/^\/customers\/(\d+)$/);
  return match ? Number(match[1]) : null;
}

function Nav() {
  const { pathname } = useDataAppLocation();
  const active = activeTab(pathname);

  return (
    <nav>
      {TABS.map((tab) => (
        <DataAppLink
          key={tab.path}
          to={tab.path}
          aria-current={tab === active ? "page" : undefined}
        >
          {tab.label}
        </DataAppLink>
      ))}
    </nav>
  );
}

function Page() {
  const { pathname } = useDataAppLocation();
  const customerId = useCustomerIdFromPath();

  if (customerId !== null) {
    return <CustomerDetail id={customerId} />;
  }
  return activeTab(pathname).render();
}

export default function App() {
  return (
    <DataAppRouter>
      <Nav />
      <Page />
    </DataAppRouter>
  );
}
```

To navigate from code, such as from a button:

```tsx
function OpenCustomerButton({ id }: { id: number }) {
  const { navigate } = useDataAppLocation();
  return <button onClick={() => navigate(`/customers/${id}`)}>Open #{id}</button>;
}
```

Run `npm run dev`, click the links, and watch the URL change. Reload at `http://localhost:5174/customers/42`: the preview should land on that route directly. Then reload at the base path. The first tab's content should show right away, with that tab marked as selected.

Nothing else is needed for the parent page's URL. Metabase mirrors each navigation to `/apps/<slug>/<path>`, and a reload at any sub-path boots the app on that route.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Navigating throws a blocked `History.pushState` call, and the diagnostics feed has a `blocked-api` entry for it. | A router library, or a direct `history` call, is in the tree. Remove it, and use `<DataAppLink>` and `navigate` from `useDataAppLocation()`. |
| Middle-click on a `<DataAppLink>` does nothing in the dev preview. | A wrapping component swallows the event. The link itself lets non-left clicks through to the browser. |
