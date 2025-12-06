'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TextSelectionPopupProps {
  ticker: string;
  onAskQuestion: (question: string, context: string) => Promise<{ answer: string; sources: any[] }>;
}

interface PopupState {
  visible: boolean;
  x: number;
  y: number;
  selectedText: string;
}

export default function TextSelectionPopup({ ticker, onAskQuestion }: TextSelectionPopupProps) {
  const [popup, setPopup] = useState<PopupState>({
    visible: false,
    x: 0,
    y: 0,
    selectedText: '',
  });
  const [showQuestionInput, setShowQuestionInput] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  // Handle text selection
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    const selectedText = selection?.toString().trim();

    if (selectedText && selectedText.length > 10 && selectedText.length < 500) {
      const range = selection?.getRangeAt(0);
      const rect = range?.getBoundingClientRect();

      if (rect) {
        setPopup({
          visible: true,
          x: rect.left + rect.width / 2,
          y: rect.top - 10,
          selectedText,
        });
        setShowQuestionInput(false);
        setAnswer(null);
        setError(null);
      }
    }
  }, []);

  // Handle click outside to close popup
  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
      // Small delay to allow button clicks to register
      setTimeout(() => {
        const selection = window.getSelection();
        if (!selection?.toString().trim()) {
          setPopup((prev) => ({ ...prev, visible: false }));
          setShowQuestionInput(false);
          setAnswer(null);
        }
      }, 100);
    }
  }, []);

  // Set up event listeners
  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [handleMouseUp, handleClickOutside]);

  // Handle asking a question
  const handleAskQuestion = async () => {
    if (!question.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      // Construct question with context
      const fullQuestion = `Regarding this text: "${popup.selectedText.substring(0, 200)}..." - ${question}`;
      const result = await onAskQuestion(fullQuestion, popup.selectedText);
      setAnswer(result.answer);
    } catch (err) {
      setError('Failed to get answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Quick question buttons
  const quickQuestions = [
    'Explain this in simple terms',
    'What are the implications?',
    'How does this compare to industry average?',
    'Is this a risk factor?',
  ];

  const handleQuickQuestion = async (q: string) => {
    setQuestion(q);
    setShowQuestionInput(true);

    setIsLoading(true);
    setError(null);

    try {
      const fullQuestion = `Regarding this text from ${ticker}'s SEC filing: "${popup.selectedText.substring(0, 300)}" - ${q}`;
      const result = await onAskQuestion(fullQuestion, popup.selectedText);
      setAnswer(result.answer);
    } catch (err) {
      setError('Failed to get answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!popup.visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        ref={popupRef}
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className="fixed z-50 bg-slate-900 border border-slate-700 rounded-lg shadow-xl"
        style={{
          left: Math.min(popup.x - 150, window.innerWidth - 320),
          top: Math.max(popup.y - (answer ? 300 : showQuestionInput ? 200 : 150), 10),
          width: '300px',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700">
          <span className="text-xs font-medium text-slate-400">
            Ask about selection
          </span>
          <button
            onClick={() => setPopup((prev) => ({ ...prev, visible: false }))}
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-3">
          {!showQuestionInput && !answer && (
            <>
              {/* Selected text preview */}
              <div className="mb-3 p-2 bg-slate-800 rounded text-xs text-slate-300 max-h-16 overflow-hidden">
                "{popup.selectedText.substring(0, 100)}..."
              </div>

              {/* Quick question buttons */}
              <div className="space-y-2">
                {quickQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleQuickQuestion(q)}
                    className="w-full text-left px-3 py-2 text-sm text-slate-300 bg-slate-800 hover:bg-slate-700 rounded transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Custom question button */}
              <button
                onClick={() => setShowQuestionInput(true)}
                className="w-full mt-2 px-3 py-2 text-sm text-primary-400 bg-primary-500/10 hover:bg-primary-500/20 rounded transition-colors flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Ask custom question
              </button>
            </>
          )}

          {showQuestionInput && !answer && (
            <>
              {/* Custom question input */}
              <div className="mb-3 p-2 bg-slate-800 rounded text-xs text-slate-300 max-h-12 overflow-hidden">
                "{popup.selectedText.substring(0, 80)}..."
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                  placeholder="Type your question..."
                  className="flex-1 px-3 py-2 text-sm bg-slate-800 border border-slate-700 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-primary-500"
                  autoFocus
                />
                <button
                  onClick={handleAskQuestion}
                  disabled={isLoading || !question.trim()}
                  className="px-3 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded transition-colors"
                >
                  {isLoading ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  )}
                </button>
              </div>
            </>
          )}

          {isLoading && (
            <div className="flex items-center justify-center py-4">
              <svg className="w-6 h-6 text-primary-400 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span className="ml-2 text-sm text-slate-400">Getting answer...</span>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-300">
              {error}
            </div>
          )}

          {answer && (
            <div className="space-y-3">
              <div className="p-2 bg-slate-800 rounded text-xs text-slate-400">
                Q: {question}
              </div>
              <div className="p-3 bg-primary-500/10 border border-primary-500/30 rounded text-sm text-slate-200 max-h-48 overflow-y-auto">
                {answer}
              </div>
              <button
                onClick={() => {
                  setAnswer(null);
                  setQuestion('');
                  setShowQuestionInput(false);
                }}
                className="w-full px-3 py-2 text-sm text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded transition-colors"
              >
                Ask another question
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
