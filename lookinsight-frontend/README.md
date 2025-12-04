# LookInsight Frontend

A Next.js 14 frontend application for SEC filing analysis platform.

## Features

- **Company Analysis**: Deep dive into SEC filings with AI-powered insights
- **Competitor Analysis**: Identify and compare companies against competitors
- **Historical Analysis**: 5-year trend analysis with red flag detection
- **Interactive Dashboard**: Tabbed interface with lazy loading
- **Responsive Design**: Mobile-first design with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Data Fetching**: SWR
- **Tables**: @tanstack/react-table
- **Markdown**: react-markdown
- **UI Components**: Custom components with headless UI patterns

## Project Structure

```
├── app/
│   ├── api/                 # API routes (proxy to Python backend)
│   ├── analysis/[ticker]/   # Company analysis pages
│   ├── layout.tsx           # Root layout
│   └── page.tsx            # Landing page
├── components/              # Reusable UI components
├── lib/                    # Utility functions and API helpers
├── styles/                 # Global CSS and Tailwind config
└── types/                  # TypeScript type definitions
```

## Getting Started

### Prerequisites

- Node.js 18.17 or later
- Python backend running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your configuration:
```env
PYTHON_API_URL=http://localhost:8000
```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## API Integration

The frontend communicates with a Python backend through API routes in `/app/api/`. These routes act as proxies and transform data to match frontend types.

### Available Endpoints

- `POST /api/analyze` - Company analysis
- `GET /api/competitors/[ticker]` - Competitor analysis
- `POST /api/compare` - Financial comparison
- `GET /api/historical` - Historical analysis with red flags

## Components

### Core Components

- **SearchBar**: Ticker input with validation
- **MetricsBar**: Financial metrics display
- **TabNavigation**: Interactive tab system with loading states
- **MarkdownDisplay**: Advanced markdown rendering with citations
- **ComparisonTable**: Sortable competitor comparison table

### Features

- **Lazy Loading**: Tabs load data only when activated
- **Error Handling**: Comprehensive error states and retry mechanisms
- **Loading States**: Skeleton screens and spinners
- **Responsive Design**: Works on all device sizes
- **Accessibility**: ARIA labels and keyboard navigation

## Styling

Uses Tailwind CSS with custom design system:

- **Primary**: Blue (#1e3a8a)
- **Success**: Green (#10b981)
- **Warning**: Amber (#f59e0b)
- **Danger**: Red (#ef4444)

## Development Notes

- Uses SWR for efficient data fetching and caching
- TypeScript strict mode enabled
- Custom markdown parser for citation handling
- Optimized for SEO with proper meta tags
- Error boundaries for graceful error handling