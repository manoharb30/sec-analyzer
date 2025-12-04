'use client';

import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { useState, useMemo } from 'react';
import { CompetitorData } from '@/types';

interface ComparisonTableProps {
  data: CompetitorData[];
  isLoading?: boolean;
}

const columnHelper = createColumnHelper<CompetitorData>();

export default function ComparisonTable({ data, isLoading }: ComparisonTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('rank', {
        header: 'Rank',
        cell: (info) => (
          <div className="flex items-center justify-center">
            <span className="inline-flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-800 rounded-full text-sm font-semibold">
              {info.getValue()}
            </span>
          </div>
        ),
        size: 80,
      }),
      columnHelper.accessor('companyName', {
        header: 'Company',
        cell: (info) => (
          <div>
            <div className="font-semibold text-gray-900">{info.getValue()}</div>
            <div className="text-sm text-gray-500 font-mono">
              {info.row.original.ticker}
            </div>
          </div>
        ),
        size: 200,
      }),
      columnHelper.accessor('businessOverlap', {
        header: 'Business Overlap',
        cell: (info) => (
          <div className="text-sm text-gray-600 leading-relaxed">
            {info.getValue()}
          </div>
        ),
        size: 300,
      }),
      columnHelper.accessor('competitiveStrength', {
        header: 'Threat Level',
        cell: (info) => {
          const strength = info.getValue();
          const getStrengthStyle = () => {
            switch (strength) {
              case 'high':
                return 'bg-danger-100 text-danger-800 border-danger-200';
              case 'medium':
                return 'bg-warning-100 text-warning-800 border-warning-200';
              case 'low':
                return 'bg-success-100 text-success-800 border-success-200';
              default:
                return 'bg-gray-100 text-gray-800 border-gray-200';
            }
          };

          return (
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getStrengthStyle()}`}
            >
              {strength.charAt(0).toUpperCase() + strength.slice(1)}
            </span>
          );
        },
        size: 120,
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="animate-pulse">
          <div className="bg-gray-50 px-6 py-4">
            <div className="h-4 bg-gray-200 rounded w-48"></div>
          </div>
          <div className="divide-y divide-gray-200">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="px-6 py-4 flex items-center space-x-4">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-32"></div>
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-64"></div>
                <div className="h-6 bg-gray-200 rounded-full w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No competitors found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            No competitor data available for this company.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Competitor Analysis ({data.length} companies)
          </h3>

          {/* Filter */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                placeholder="Filter companies..."
                value={
                  (table.getColumn('companyName')?.getFilterValue() as string) ?? ''
                }
                onChange={(event) =>
                  table.getColumn('companyName')?.setFilterValue(event.target.value)
                }
                className="w-64 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={header.column.getToggleSortingHandler()}
                    style={{ width: header.getSize() }}
                  >
                    <div className="flex items-center space-x-1">
                      <span>
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </span>
                      {header.column.getCanSort() && (
                        <span className="text-gray-400">
                          {{
                            asc: '↑',
                            desc: '↓',
                          }[header.column.getIsSorted() as string] ?? '↕'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-gray-50 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-6 py-4 whitespace-nowrap align-top"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {data.length > 0 && (
        <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-700">
            <span>
              Showing {table.getRowModel().rows.length} of {data.length} competitors
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">
                Ranked by competitive threat level
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}