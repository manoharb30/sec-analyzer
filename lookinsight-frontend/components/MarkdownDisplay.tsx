'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MarkdownParser, ParsedMarkdown } from '@/lib/markdown-parser';
import CitationTooltip from './CitationTooltip';

interface MarkdownDisplayProps {
  content: string;
  showCollapsibleSections?: boolean;
  highlightRisks?: boolean;
}

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  level: number;
}

function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  level
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const getHeaderClass = () => {
    switch (level) {
      case 1:
        return 'text-2xl font-bold text-gray-900';
      case 2:
        return 'text-xl font-semibold text-gray-800';
      case 3:
        return 'text-lg font-medium text-gray-700';
      default:
        return 'text-base font-medium text-gray-600';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors duration-200 flex items-center justify-between rounded-t-lg"
      >
        <h3 className={getHeaderClass()}>{title}</h3>
        <svg
          className={`w-5 h-5 text-gray-500 transform transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isOpen && (
        <div className="px-4 py-3 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
}

export default function MarkdownDisplay({
  content,
  showCollapsibleSections = true,
  highlightRisks = true
}: MarkdownDisplayProps) {
  const [parsedContent, setParsedContent] = useState<ParsedMarkdown | null>(null);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);

  useEffect(() => {
    if (content) {
      const parsed = MarkdownParser.parse(content);
      setParsedContent(parsed);
    }
  }, [content]);

  const handleCitationClick = (citationId: string) => {
    setActiveCitation(activeCitation === citationId ? null : citationId);
  };

  if (!content) {
    return (
      <div className="flex items-center justify-center py-12">
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No content</h3>
          <p className="mt-1 text-sm text-gray-500">
            No analysis content available for this section.
          </p>
        </div>
      </div>
    );
  }

  if (showCollapsibleSections && parsedContent?.sections && parsedContent.sections.length > 1) {
    return (
      <div className="space-y-4">
        {parsedContent.sections.map((section, index) => (
          <CollapsibleSection
            key={section.id}
            title={section.title}
            level={section.level}
            defaultOpen={index === 0} // Open first section by default
          >
            <div className="markdown-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom table styling
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full border border-gray-300">
                        {children}
                      </table>
                    </div>
                  ),
                  // Custom citation handling
                  sup: ({ children, ...props }) => {
                    const citationId = (props as any)['data-citation-id'];
                    if (citationId) {
                      return (
                        <sup
                          className="citation"
                          onClick={() => handleCitationClick(citationId)}
                          {...props}
                        >
                          {children}
                        </sup>
                      );
                    }
                    return <sup {...props}>{children}</sup>;
                  },
                  // Custom link styling
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-800 underline"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {section.content}
              </ReactMarkdown>
            </div>
          </CollapsibleSection>
        ))}

        {/* Citations */}
        {parsedContent.citations.length > 0 && (
          <CitationTooltip
            citations={parsedContent.citations}
            activeCitation={activeCitation}
            onClose={() => setActiveCitation(null)}
          />
        )}
      </div>
    );
  }

  // Regular markdown display without collapsible sections
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border border-gray-300">
                {children}
              </table>
            </div>
          ),
          sup: ({ children, ...props }) => {
            const citationId = (props as any)['data-citation-id'];
            if (citationId) {
              return (
                <sup
                  className="citation"
                  onClick={() => handleCitationClick(citationId)}
                  {...props}
                >
                  {children}
                </sup>
              );
            }
            return <sup {...props}>{children}</sup>;
          },
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-800 underline"
            >
              {children}
            </a>
          ),
        }}
      >
        {parsedContent?.content || content}
      </ReactMarkdown>

      {/* Citations */}
      {parsedContent?.citations && parsedContent.citations.length > 0 && (
        <CitationTooltip
          citations={parsedContent.citations}
          activeCitation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      )}
    </div>
  );
}