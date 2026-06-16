// src/modules/users/components/AppTable.tsx
import React from "react";
import classNames from "classnames";

type Column<T> = {
  header: string;
  accessor: ((row: T) => React.ReactNode) | keyof T;
  className?: string;
  width?: string;
};

interface AppTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: string | null;
}

export function AppTable<T>({ columns, data, loading, error }: AppTableProps<T>) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-200 rounded w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-600">
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">No records found.</div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={classNames(
                  "px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                  col.className
                )}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-card divide-y divide-gray-100">
          {data.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-gray-50 transition-colors">
              {columns.map((col, colIdx) => {
                const cellContent =
                  typeof col.accessor === "function"
                    ? col.accessor(row)
                    : (row[col.accessor as keyof T] as React.ReactNode);
                return (
                  <td key={colIdx} className={classNames("px-4 py-2", col.className)}>
                    {cellContent}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AppTable;


