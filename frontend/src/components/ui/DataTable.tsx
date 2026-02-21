import type { ReactNode } from "react";

interface Column<TItem> {
  key: string;
  header: string;
  render: (item: TItem) => ReactNode;
  className?: string;
}

interface DataTableProps<TItem> {
  columns: Column<TItem>[];
  items: TItem[];
  rowKey: (item: TItem) => string;
  onRowClick?: (item: TItem) => void;
  selectedRowKey?: string | null;
}

export function DataTable<TItem>({
  columns,
  items,
  rowKey,
  onRowClick,
  selectedRowKey
}: DataTableProps<TItem>) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface-0)]">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-[var(--surface-2)] text-[var(--ink-1)]">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={`px-3 py-2 font-semibold ${column.className ?? ""}`}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={rowKey(item)}
              className={[
                "border-t border-[var(--border)] align-top",
                onRowClick ? "cursor-pointer hover:bg-[var(--surface-2)]" : "",
                selectedRowKey === rowKey(item) ? "bg-[var(--brand-soft)]/50" : ""
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={onRowClick ? () => onRowClick(item) : undefined}
            >
              {columns.map((column) => (
                <td key={column.key} className={`px-3 py-2 text-[var(--ink-0)] ${column.className ?? ""}`}>
                  {column.render(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
