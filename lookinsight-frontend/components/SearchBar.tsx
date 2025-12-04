'use client';

import { useState, useRef, useEffect } from 'react';

interface SearchBarProps {
  onAnalyze: (ticker: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  showSuggestions?: boolean;
}

// Common ticker symbols for autocomplete
const popularTickers = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA',
  'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS',
  'CTAS', 'FAST', 'POOL', 'CHE', 'LANC', 'ROP', 'WSM', 'SEIC'
];

export default function SearchBar({
  onAnalyze,
  isLoading = false,
  placeholder = "Enter ticker symbol",
  showSuggestions = false
}: SearchBarProps) {
  const [ticker, setTicker] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestionsList, setShowSuggestionsList] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showSuggestions && ticker.length > 0) {
      const filtered = popularTickers.filter(t =>
        t.toLowerCase().includes(ticker.toLowerCase())
      ).slice(0, 8);
      setSuggestions(filtered);
      setShowSuggestionsList(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestionsList(false);
    }
    setSelectedIndex(-1);
  }, [ticker, showSuggestions]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onAnalyze(ticker.trim().toUpperCase());
      setShowSuggestionsList(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setTicker(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestionsList) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        if (selectedIndex >= 0) {
          e.preventDefault();
          setTicker(suggestions[selectedIndex]);
          setShowSuggestionsList(false);
          onAnalyze(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestionsList(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setTicker(suggestion);
    setShowSuggestionsList(false);
    onAnalyze(suggestion);
  };

  const handleBlur = (e: React.FocusEvent) => {
    // Delay hiding suggestions to allow click events
    setTimeout(() => {
      if (!suggestionsRef.current?.contains(e.relatedTarget as Node)) {
        setShowSuggestionsList(false);
      }
    }, 150);
  };

  return (
    <div className="relative w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={ticker}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onFocus={() => {
              if (showSuggestions && suggestions.length > 0) {
                setShowSuggestionsList(true);
              }
            }}
            placeholder={placeholder}
            className="input-field text-lg font-mono tracking-wider"
            disabled={isLoading}
            maxLength={10}
            autoComplete="off"
            spellCheck={false}
          />

          {/* Suggestions Dropdown */}
          {showSuggestionsList && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-lg shadow-lg z-50 mt-1 max-h-64 overflow-y-auto"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors font-mono tracking-wider ${
                    index === selectedIndex ? 'bg-primary-50 text-primary-900' : 'text-gray-700'
                  } ${index === 0 ? 'rounded-t-lg' : ''} ${
                    index === suggestions.length - 1 ? 'rounded-b-lg' : ''
                  }`}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading || !ticker.trim()}
          className="btn-primary min-w-[120px] flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4"
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
              Analyzing...
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </form>

      {/* Validation Message */}
      {ticker && ticker.length > 6 && (
        <p className="text-warning-600 text-sm mt-2">
          Ticker symbols are typically 1-5 characters long
        </p>
      )}
    </div>
  );
}