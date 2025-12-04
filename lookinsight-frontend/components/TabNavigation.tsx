'use client';

import { TabType } from '@/types';

interface TabNavigationProps {
  tabs: TabType[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export default function TabNavigation({ tabs, activeTab, onTabChange }: TabNavigationProps) {
  return (
    <div className="bg-slate-950/50 border-b border-white/10">
      <div className="px-4 sm:px-6 lg:px-8">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const hasError = tab.error;
            const isLoading = tab.isLoading;

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                disabled={isLoading}
                className={`
                  group relative min-w-0 flex-1 overflow-hidden bg-transparent py-4 px-1 text-center text-sm font-medium border-b-2 focus:z-10 focus:outline-none transition-colors
                  ${
                    isActive
                      ? 'border-primary-400 text-primary-300'
                      : hasError
                      ? 'border-transparent text-danger-300 hover:text-danger-200 hover:border-danger-400/50'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-400/50'
                  }
                  ${isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                `}
                aria-current={isActive ? 'page' : undefined}
              >
                <div className="flex items-center justify-center space-x-2">
                  <span>{tab.label}</span>

                  {/* Loading indicator */}
                  {isLoading && (
                    <svg
                      className="animate-spin h-4 w-4 text-current"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  )}

                  {/* Error indicator */}
                  {hasError && !isLoading && (
                    <svg
                      className="h-4 w-4 text-danger-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  )}

                  {/* Success indicator for completed tabs */}
                  {!isLoading && !hasError && tab.content && !isActive && (
                    <svg
                      className="h-4 w-4 text-success-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>

                {/* Active tab indicator */}
                {isActive && (
                  <span
                    className="absolute inset-x-0 bottom-0 h-0.5 bg-primary-400"
                    aria-hidden="true"
                  />
                )}

                {/* Hover indicator for inactive tabs */}
                {!isActive && (
                  <span
                    className="absolute inset-x-0 bottom-0 h-0.5 bg-transparent group-hover:bg-slate-400/50 transition-colors"
                    aria-hidden="true"
                  />
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}