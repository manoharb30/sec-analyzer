'use client';

import { Citation } from '@/lib/markdown-parser';

interface CitationTooltipProps {
  citations: Citation[];
  activeCitation: string | null;
  onClose: () => void;
}

export default function CitationTooltip({
  citations,
  activeCitation,
  onClose
}: CitationTooltipProps) {
  const activeCitationData = citations.find(c => c.id === activeCitation);

  if (!activeCitationData) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-25 z-40"
        onClick={onClose}
      />

      {/* Citation Modal */}
      <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md bg-white rounded-lg shadow-xl border border-gray-200 z-50">
        <div className="p-4">
          <div className="flex items-start justify-between mb-3">
            <h4 className="text-lg font-semibold text-gray-900">Citation</h4>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-700">Source:</span>
              <p className="text-sm text-gray-600 mt-1">
                {activeCitationData.source || activeCitationData.text}
              </p>
            </div>

            {activeCitationData.url && (
              <div>
                <span className="text-sm font-medium text-gray-700">Link:</span>
                <a
                  href={activeCitationData.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-primary-600 hover:text-primary-800 underline mt-1 break-all"
                >
                  {activeCitationData.url}
                </a>
              </div>
            )}

            {activeCitationData.url && (
              <div className="pt-2 border-t border-gray-200">
                <a
                  href={activeCitationData.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-sm text-primary-600 hover:text-primary-800 transition-colors"
                >
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                  Open source
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}