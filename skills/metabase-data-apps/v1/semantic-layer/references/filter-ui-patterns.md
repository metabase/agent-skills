# Filter controls

Code for the controls that `semantic-layer.md`, _Filters_ under _Rules_, describes. The rules live there.

## Runtime options

Declare the options query in `queries/` like any other query, with a breakout on the same field or metric dimension that the filter applies, and run it with `useMetabaseQuery`. Derive a deduped option list from its rows. Query options from the same source the cards use, so the list stays compatible with the filter. For a metric-backed card, use the metric's dimension in both the options query and the card's query:

```ts
// queries/revenue.query.ts
const ordersTable = schema.tables.orders;
const revenueMetric = schema.metrics.revenue;
const franchiseDimension = revenueMetric.dimensions.orders.franchiseId;

export const RevenueByFranchise = defineQuery({
  source: ordersTable,
  aggregations: [revenueMetric],
  breakouts: [breakout(franchiseDimension)],
});

// the filter bar
const { data: optionData } = useMetabaseQuery(RevenueByFranchise);

const revenueFilters =
  selectedFranchise === "all"
    ? []
    : [filter(franchiseDimension, "=", selectedFranchise)];
```

Keep the label and the raw value apart, and pass `value` to `filter(...)`:

```ts
type Option = { label: string; value: string };

const franchiseOptions = rows.map((row) => ({
  label: row.franchise_name ?? row.franchise_id,
  value: row.franchise_id,
}));
```

When fresh options no longer hold the selected value, reset it:

```tsx
useEffect(() => {
  if (
    selectedValue !== "all" &&
    !options.some((option) => option.value === selectedValue)
  ) {
    setSelectedValue("all");
  }
}, [options, selectedValue]);
```

While options load, render All plus a loading or empty row for the dynamic values, with All still enabled.

## Searchable combobox

If the app has no combobox component, prefer a small established combobox or listbox dependency, or the app's component library, for keyboard, focus, and positioning behavior. Hand-roll only a small one: an input, a capped list, mouse selection, closing on Escape or blur, and a clear button. Either way:

- Click or focus opens the list right away, before any typing.
- Search matches labels, not raw ids.
- All is always an option.
- Selecting an option stores its raw `value`.
- The list is capped or scrolls, so it can't stretch the page.
- It's styled like the app's other controls.

Don't close the list from an `onBlur` on the trigger button when the popover holds an auto-focused input: moving focus into the input blurs the button and closes the list at once. Keep focus within one wrapper and close only when focus leaves the whole wrapper, or close on selection, Escape, and outside clicks.

## Date range: `DateRangePopover`

`DateRangePopover` wraps the app's own trigger and opens a Metabase-styled range calendar under it. The trigger is yours, a button styled like the preset buttons beside it. The SDK owns the calendar, its positioning, and closing on outside clicks and Escape. It needs no dependency and no CSS import.

```tsx
import {
  DateRangePopover,
  useDateFormatter,
} from "@metabase/embedding-sdk-react/data-app";

const { formatDateRange } = useDateFormatter();
const [range, setRange] = useState<[string | null, string | null]>([null, null]);
const [start, end] = range;

const dateFilters =
  start && end
    ? [filter(ordersTable.fields.createdAt, "between", [start, end])]
    : [];

<DateRangePopover value={range} onChange={setRange}>
  <button className="filter-button">
    {formatDateRange(range) || "Custom"}
  </button>
</DateRangePopover>;
```

- Both ends are `YYYY-MM-DD` strings, the shape `filter(...)` takes, so there's no `Date` conversion and no time zone to get wrong.
- The trigger must be a single DOM element or a `forwardRef` component, since the popover attaches a ref and a click handler to it.
- Label the trigger with `formatDateRange(range)` from `useDateFormatter()`, which parses in local time and formats in the instance's locale, the same way Metabase's own date input labels itself. Never use `new Date("YYYY-MM-DD")`: a date-only string parses as UTC and shows the previous day west of Greenwich. `formatDateRange` returns `""` until the SDK bundle loads, then re-renders the trigger. Its three states are `""`, `"September 1, 2026 – "`, and `"September 1, 2026 – September 10, 2026"`. `formatDate` formats one end. Both take `format` (a dayjs format), and `formatDateRange` also takes `separator`.
- `onChange` fires on every calendar click, so a half-picked range arrives as `[start, null]`.
- The popover closes itself once both ends are picked (`closeOnSelect`, default `true`). Pass `opened` and `onOpenedChange` to control it yourself.
- Other props: `defaultValue`, `minDate` and `maxDate` (`YYYY-MM-DD`), `numberOfColumns` (months side by side, default 2), and `position` (default `bottom-start`).
- `DateRangeCalendar` is the same calendar without the popover, for a container the app already has. It takes the same value props, plus `className` and `style`.

A native `<input type="date">` won't do, because its placeholder and calendar are browser-controlled, often show `mm/dd/yyyy`, and can't be themed reliably.

## Single dates and date-times: `react-datepicker`

Only for what the SDK calendar doesn't cover, such as picking a single date or a date and time. Nothing else justifies a picker dependency: `react-datepicker`, `react-day-picker`, `flatpickr`, `@mui/x-date-pickers`, `antd`, and `rsuite` are all the same mistake for a plain date range, and so is a whole UI suite installed for one filter. `react-datepicker` is the default pick:

```bash
npm install react-datepicker
```

- Import `react-datepicker/dist/react-datepicker.css`, then add small CSS overrides for the app's style if needed.
- Type strict callbacks explicitly, such as `onChange={(date: Date | null) => ...}` for a single date.
- Convert a picked `Date` to `YYYY-MM-DD` with the local getters (`getFullYear`, `getMonth`, `getDate`), never `toISOString()`, which shifts the day.
- Parse saved strings for `selected` defensively, and pass `null` for an empty or invalid value. Never pass `new Date("")`.
- Recent versions ship their own types. Don't add `@types/react-datepicker` unless the installed version needs it.
