# Run Metabase actions from a data app

A Metabase **action** is a saved, parameterized SQL write against the data warehouse: an `INSERT`, `UPDATE`, or `DELETE`, configured on the instance with its parameters and permissions. A data app **invokes** one with the right parameters when the user clicks a button, submits a form, or confirms a destructive prompt.

## What's in the schema

The schema is the complete catalog of the actions the app can run. Each is `schema.actions.<actionName>`, with `type: "query"` and a `parameters` list. Each parameter has a `slug` (the key the app sends), a `displayName` (for labels, never a key), a `jsType` (`"string"`, `"number"`, `"Date"`, `"boolean"`, or `"unknown"`), and an optional `required` flag. Slugs are whatever the action's author named the SQL parameters, so read them from the schema.

List `schema.actions` before writing any action code. An action that isn't there doesn't exist for the app. Never fake the call. When the app needs a write the schema lacks, draft a query action without a model (`mb skills get data-action`; an action created from a model in the Metabase UI belongs to that model and is never listed). Show the user its SQL and parameters, and if they say yes, run `mb data-action create`. An action runs only on a database whose **Data actions** toggle is on: Admin > Databases > <database>, or `mb db set-data-actions <db-id> true` in an `mb` whose `mb db --help` lists that command. Then regenerate the schema.

## The definition and the hook

```ts
// actions/people.action.ts
import { defineAction } from "@metabase/embedding-sdk-react/data-app";
import schema from "../src/metabase.data";

export const CreatePerson = defineAction({
  copiedActionEntityId: "<from npx @metabase/representations generate-entity-id>",
  action: schema.actions.createPerson,
});
```

A production build runs the action's copy in the app's collection, which `npm run write-resources` writes, as in `semantic-layer/semantic-layer.md`, _Write every query and action into the app's collection_. Read that section before running it: it covers how the command fails and how to fix what `check-resources` reports.

```ts
import { useAction } from "@metabase/embedding-sdk-react/data-app";
import { CreatePerson } from "../../actions/people.action";

const { execute, isExecuting, result, error, reset } = useAction(CreatePerson);
```

- **Import `useAction` from `@metabase/embedding-sdk-react/data-app`.** That entry's hook takes only a `defineAction(...)` export, or `null`. The main entry's `useAction` is the general SDK hook: it also takes plain objects and raw ids, so the definition check never runs. In a data app, a raw id still fails at runtime with "was passed to `useAction` as a raw id".
- **Write no generics.** The definition carries its schema entry, so the hook infers `execute`'s parameters object (keyed by `slug`, with `required: true` entries as required keys, each typed from its `jsType`) and the type of `result`.
- **`execute(parameters)`** runs the action. It resolves to the response body on success, and on failure it both throws and sets `error`. It resolves to `null`, without making a request, when the action is `null` or the SDK hasn't initialized, so guard the call site if either can happen. The hook never runs on mount and takes no `enabled` option: to skip the action, return early in the event handler.
- **`isExecuting`** is `true` from the call until it settles. Drive the trigger's `disabled` from it, and show a spinner in the button, so a double click can't send duplicate requests.
- **`result`** is the response body, `null` before the first call and after `reset()`. Use `result?.["rows-affected"]` for a lightweight confirmation, then refresh the data on screen.
- **`error`** is the last failure, typed `ActionExecuteError | null`, with the shape `{ status?, data: { message?, errors? }, isCancelled }`. Read its fields directly, without a cast.
- **`reset()`** clears `result` and `error`, such as after the user dismisses a message.

## A form that writes a row

```tsx
import { useAction } from "@metabase/embedding-sdk-react/data-app";
import { useState, type FormEvent } from "react";

import { CreatePerson } from "../../actions/people.action";

export function AddPersonForm({ onCreated }: { onCreated: () => Promise<void> }) {
  const { execute, isExecuting, error } = useAction(CreatePerson);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [isFormValid, setIsFormValid] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await execute({ name, email }); // keys are the parameter slugs
      setName("");
      setEmail("");
      setIsFormValid(false);
      await onCreated(); // the parent refetches what the action changed
    } catch {
      // the failure is also in `error`, rendered below
    }
  }

  return (
    // both parameters are `required: true` in this action's schema entry
    <form
      onSubmit={onSubmit}
      onChange={(event) => setIsFormValid(event.currentTarget.checkValidity())}
    >
      <input type="text" required value={name} onChange={(e) => setName(e.target.value)} />
      <input type="text" required value={email} onChange={(e) => setEmail(e.target.value)} />
      <button type="submit" disabled={isExecuting || !isFormValid}>
        {isExecuting ? "Saving…" : "Add"}
      </button>
      {error ? (
        <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
          {error.data.message ?? "Action failed."}
        </pre>
      ) : null}
    </form>
  );
}
```

## Map the parameters to inputs

Pick each input's `type` from the parameter's `jsType`, never from its slug: a slug called `phone` or `email` with `jsType: "string"` is still `type="text"`.

| `jsType` | Input |
| --- | --- |
| `"string"` | `<input type="text">` |
| `"number"` | `<input type="number">` |
| `"boolean"` | `<input type="checkbox">`, or a `Switch` or `Checkbox` component |
| `"Date"` | `<input type="date">`, or `"datetime-local"` when a time is expected |
| `"unknown"` | `<input type="text">`, coerced at the call site |

Values in `execute({ … })` match their `jsType`. A `"number"` parameter wants a `number`, but `<input>.value` is always a string, so read `.valueAsNumber` or coerce with `Number(...)`. Coerce booleans the same way.

## Validate only what the schema says

The schema's validation contract is `parameter.required`, plus `jsType` for coercion, which matches Metabase's own action form. Set `required={parameter.required}` on each input, and nothing more. No length, range, or format checks, and no `required` or `type="email"` because a slug is called `email`. Anything stricter comes back from the backend as an error after submit. Disable the submit button from the browser's own verdict, `form.checkValidity()`, as above, never from hand-rolled checks such as `!name || !email`.

## Show the error message

Render both layers of `error`. `error.data.message` is the whole-request failure, which covers every failure of the SQL itself. `error.data.errors`, when present, maps a parameter slug to its validation message. Query actions usually leave it out, so read it as `error?.data.errors ?? {}`. Render the message in a `<pre>`, or any element with `white-space: pre-wrap`: driver errors often span several lines, and a `<span>` collapses them.

```tsx
const fieldErrors = error?.data.errors ?? {};

{action.parameters.map((parameter) => {
  const fieldError = fieldErrors[parameter.slug];
  return (
    <label key={parameter.slug}>
      {parameter.displayName}
      <input
        required={parameter.required}
        aria-invalid={Boolean(fieldError)}
        style={{ borderColor: fieldError ? "#dc2626" : undefined }}
      />
      {fieldError ? <div role="alert">{fieldError}</div> : null}
    </label>
  );
})}
```

A failing query action comes back with status 500, and an `error.data.message` that wraps the driver's own text: `Error executing Action: Error executing write query: <the driver's message>`. Render it as it is. Never replace it with "Failed", "Something went wrong", or `String(error)`, and never paraphrase it into something friendlier: the raw message is the only fix-it information the user has. When a field has its own message in `error.data.errors`, show it beside that field too.

## Refresh after the action

After an action succeeds, refresh every piece of data on screen that it could have changed. Without a refresh, the list keeps the old rows and the tile the old count, with no warning. The refresh is the `refetch` that `useMetabaseQuery` returns beside `data`: `await execute(...)`, then `await Promise.all([ordersQuery.refetch(), totalsQuery.refetch()])`.

- Run the data hooks in a component above the trigger, and pass the refresh down. A hook in the same component as the trigger, or below it, can't be wired to it.
- Await the refresh, so the form doesn't clear and the modal doesn't close before the fresh data arrives.
- Never prepend `result` to a local list instead of refreshing. Server-filled values, such as generated IDs, timestamps, and computed or joined columns, differ from any guess.

## Debugging

When an action seems to succeed but the screen doesn't update, or a call fails:

1. Log `result`, `error`, and `isExecuting` after `await execute(...)` to confirm the request went through.
2. Confirm that `useAction` got the `defineAction(...)` export from `actions/`. Its `.id` is a type error with the `/data-app` hook. The main entry's hook accepts it untyped, and then fails at runtime with "was passed to `useAction` as a raw id". "This action has no copy" means the definition was made inside a component, or a definition in `actions/` lacks its `copiedActionEntityId`.
3. Log the object passed to `execute`. Every key must be a parameter `slug` from `schema.actions.<action>.parameters`, and every value must match its `jsType`.
4. List every view on screen that reads the rows the action writes. Confirm that each one's hook sits above the trigger, and that its `refetch` is awaited after `execute`, all of them together in `Promise.all`.
5. If the schema doesn't list an action you expect, either the action isn't defined on the instance or the schema file is stale. Regenerate the schema.
