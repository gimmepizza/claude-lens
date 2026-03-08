import React, { useState, useRef, useEffect, useCallback } from 'react';

const QUICK_ACTIONS = [
  'Summarize this page',
  'Find key terms',
  'Explain annotations',
  'Extract tables',
];

const GREETING = {
  role: 'assistant',
  content:
    "Hi! I'm your PDF markup assistant. I can help summarize pages, explain content, extract data, or answer questions about your document. How can I help?",
};

function describeAnnotations(annotations, currentPage) {
  const pageAnns = annotations.filter((a) => a.page === currentPage);
  const allAnns = annotations;

  if (allAnns.length === 0) {
    return 'No annotations have been made yet.';
  }

  const typeCounts = (list) => {
    const counts = {};
    list.forEach((a) => {
      counts[a.type] = (counts[a.type] || 0) + 1;
    });
    return counts;
  };

  const formatCounts = (counts) =>
    Object.entries(counts)
      .map(([type, count]) => {
        const label =
          type === 'highlight'
            ? 'highlight(s)'
            : type === 'box'
            ? 'rectangle(s)'
            : 'note(s)';
        return `${count} ${label}`;
      })
      .join(', ');

  const pageCounts = typeCounts(pageAnns);
  const allCounts = typeCounts(allAnns);

  const notes = allAnns.filter((a) => a.type === 'note' && a.text);
  const notesSummary =
    notes.length > 0
      ? '\n\nNotes:\n' +
        notes
          .map(
            (n) =>
              `- Page ${n.page}: "${n.text}" (at ${Math.round(n.x)}%, ${Math.round(n.y)}%)`
          )
          .join('\n')
      : '';

  let summary = `Current page ${currentPage}: ${pageAnns.length > 0 ? formatCounts(pageCounts) : 'no annotations'}.`;
  if (allAnns.length !== pageAnns.length) {
    summary += `\nAll pages: ${formatCounts(allCounts)} (${allAnns.length} total).`;
  }
  summary += notesSummary;

  return summary;
}

function generateResponse(userMsg, annotations, currentPage) {
  const lower = userMsg.toLowerCase();
  const annotationInfo = describeAnnotations(annotations, currentPage);

  if (lower.includes('summarize') || lower.includes('summary')) {
    return `Here's a summary of page ${currentPage}: This page contains document content that could include text, figures, and data.\n\n**Your annotations:**\n${annotationInfo}\n\nFor a detailed AI-powered summary, connect this assistant to a Claude API endpoint.`;
  }

  if (lower.includes('key term') || lower.includes('keyword')) {
    return `To extract key terms from page ${currentPage}, I would analyze the text content for frequently occurring domain-specific terminology.\n\n**Your annotations:**\n${annotationInfo}\n\nConnect to the Claude API for full extraction capabilities.`;
  }

  if (
    lower.includes('annotation') ||
    lower.includes('markup') ||
    lower.includes('highlight') ||
    lower.includes('rectangle') ||
    lower.includes('note')
  ) {
    return `**Annotation details:**\n${annotationInfo}\n\nYou can add highlights (yellow overlay), rectangles (red borders), or pinned notes using the toolbar. Click any annotation to remove it.`;
  }

  if (lower.includes('table') || lower.includes('extract')) {
    return `Table extraction requires analyzing the page layout to identify structured data regions. You can mark table areas using the rectangle tool, then I can help parse them.\n\n**Your annotations:**\n${annotationInfo}\n\nFull extraction is available via the Claude API.`;
  }

  if (lower.includes('help') || lower.includes('how')) {
    return `Here's what I can help with:\n\n- **Summarize**: Get a quick overview of the current page\n- **Key Terms**: Identify important terminology\n- **Annotations**: Review and manage your markups\n- **Extract**: Pull tables and structured data\n\nUse the toolbar to highlight, draw boxes, or add notes to the PDF.\n\n**Current annotations:**\n${annotationInfo}`;
  }

  return `I understand you're asking about "${userMsg}".\n\n**Your annotations:**\n${annotationInfo}\n\nI can assist with PDF analysis, annotation management, and content extraction. For full AI capabilities, connect this assistant to a Claude API endpoint.`;
}

export default function FloatingAssistant({ annotations, currentPage }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const sendMessage = useCallback(
    (text) => {
      if (!text.trim()) return;

      const userMessage = { role: 'user', content: text.trim() };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsTyping(true);

      // Simulate assistant response delay
      setTimeout(() => {
        const response = generateResponse(text, annotations, currentPage);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response },
        ]);
        setIsTyping(false);
      }, 800 + Math.random() * 600);
    },
    [annotations, currentPage]
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <>
      {/* Floating panel */}
      {isOpen && (
        <div className="assistant-panel">
          <div className="assistant-panel__header">
            <div className="assistant-panel__avatar">&#9672;</div>
            <div>
              <div className="assistant-panel__title">Claude Lens AI</div>
              <div className="assistant-panel__subtitle">
                PDF Markup Assistant
              </div>
            </div>
            <button
              className="assistant-panel__close"
              onClick={() => setIsOpen(false)}
            >
              &#10005;
            </button>
          </div>

          <div className="assistant-panel__messages">
            {messages.map((msg, i) => (
              <div key={i} className={`msg msg--${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {isTyping && (
              <div className="msg msg--assistant">
                <div className="msg__typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="assistant-panel__quick-actions">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action}
                className="quick-action-btn"
                onClick={() => sendMessage(action)}
              >
                {action}
              </button>
            ))}
          </div>

          <form className="assistant-panel__input-area" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              className="assistant-panel__input"
              type="text"
              placeholder="Ask about your PDF..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              className="assistant-panel__send"
              type="submit"
              disabled={!input.trim()}
            >
              &#9654;
            </button>
          </form>
        </div>
      )}

      {/* FAB */}
      <button
        className={`fab ${isOpen ? 'fab--open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title={isOpen ? 'Close assistant' : 'Open AI assistant'}
      >
        {isOpen ? '+' : '\u2726'}
      </button>
    </>
  );
}
