import { RedFlag } from '@/types';

export interface ParsedMarkdown {
  content: string;
  citations: Citation[];
  sections: Section[];
  redFlags: RedFlag[];
  metrics: { [key: string]: string };
}

export interface Citation {
  id: string;
  text: string;
  url?: string;
  source?: string;
}

export interface Section {
  id: string;
  title: string;
  content: string;
  level: number;
}

export class MarkdownParser {
  static parseCitations(content: string): Citation[] {
    const citations: Citation[] = [];
    const citationRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    let match;

    while ((match = citationRegex.exec(content)) !== null) {
      citations.push({
        id: `citation-${citations.length + 1}`,
        text: match[1],
        url: match[2],
        source: match[1],
      });
    }

    return citations;
  }

  static parseSections(content: string): Section[] {
    const sections: Section[] = [];
    const lines = content.split('\n');
    let currentSection: Section | null = null;
    let sectionContent: string[] = [];

    for (const line of lines) {
      const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);

      if (headerMatch) {
        // Save previous section
        if (currentSection) {
          currentSection.content = sectionContent.join('\n').trim();
          sections.push(currentSection);
        }

        // Start new section
        const level = headerMatch[1].length;
        const title = headerMatch[2];
        const id = title.toLowerCase().replace(/[^a-z0-9]+/g, '-');

        currentSection = {
          id,
          title,
          content: '',
          level,
        };
        sectionContent = [];
      } else {
        sectionContent.push(line);
      }
    }

    // Add last section
    if (currentSection) {
      currentSection.content = sectionContent.join('\n').trim();
      sections.push(currentSection);
    }

    return sections;
  }

  static parseRedFlags(content: string): RedFlag[] {
    const redFlags: RedFlag[] = [];
    const lines = content.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Look for risk patterns
      const riskMatch = line.match(/(?:high|medium|low)\s+risk/i);
      if (riskMatch) {
        const severity = riskMatch[0].split(' ')[0].toLowerCase() as 'high' | 'medium' | 'low';

        // Extract category based on context
        let category: RedFlag['category'] = 'business';
        if (line.toLowerCase().includes('accounting') || line.toLowerCase().includes('revenue recognition')) {
          category = 'accounting';
        } else if (line.toLowerCase().includes('cfo') || line.toLowerCase().includes('executive')) {
          category = 'executive';
        } else if (line.toLowerCase().includes('dso') || line.toLowerCase().includes('inventory')) {
          category = 'operational';
        } else if (line.toLowerCase().includes('cash flow')) {
          category = 'cashflow';
        }

        redFlags.push({
          category,
          severity,
          description: line.trim(),
          details: lines[i + 1]?.trim() || '',
        });
      }
    }

    return redFlags;
  }

  static parseMetrics(content: string): { [key: string]: string } {
    const metrics: { [key: string]: string } = {};
    const lines = content.split('\n');

    for (const line of lines) {
      // Look for metric patterns like "Revenue: $10.34B" or "ROE: 46.2%"
      const metricMatch = line.match(/(?:Revenue|ROE|ROA|Margin|FCF|Debt)[^:]*:\s*([^\s,]+)/i);
      if (metricMatch) {
        const key = line.split(':')[0].trim();
        const value = metricMatch[1];
        metrics[key] = value;
      }
    }

    return metrics;
  }

  static addCitationLinks(content: string, citations: Citation[]): string {
    let processedContent = content;

    citations.forEach((citation, index) => {
      const citationNumber = index + 1;
      const linkPattern = new RegExp(`\\[${citation.text}\\]\\(${citation.url}\\)`, 'g');

      processedContent = processedContent.replace(
        linkPattern,
        `${citation.text}<sup class="citation" data-citation-id="${citation.id}" title="${citation.source}">${citationNumber}</sup>`
      );
    });

    return processedContent;
  }

  static highlightRiskLevels(content: string): string {
    return content
      .replace(/\b(high risk)\b/gi, '<span class="risk-high px-2 py-1 rounded-md border">$1</span>')
      .replace(/\b(medium risk)\b/gi, '<span class="risk-medium px-2 py-1 rounded-md border">$1</span>')
      .replace(/\b(low risk)\b/gi, '<span class="risk-low px-2 py-1 rounded-md border">$1</span>');
  }

  static parse(content: string): ParsedMarkdown {
    const citations = this.parseCitations(content);
    const sections = this.parseSections(content);
    const redFlags = this.parseRedFlags(content);
    const metrics = this.parseMetrics(content);

    let processedContent = content;
    processedContent = this.addCitationLinks(processedContent, citations);
    processedContent = this.highlightRiskLevels(processedContent);

    return {
      content: processedContent,
      citations,
      sections,
      redFlags,
      metrics,
    };
  }
}