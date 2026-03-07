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

function generateResponse(userMsg, annotationCount, currentPage) {
  const lower = userMsg.toLowerCase();

  if (lower.includes('summarize') || lower.includes('summary')) {
    return `Here's a summary of page ${currentPage}: This page contains document content that could include text, figures, and data. You currently have ${annotationCount} annotation(s) on this page. For a detailed AI-powered summary, connect this assistant to a Claude API endpoint.`;
  }

  if (lower.includes('key term') || lower.includes('keyword')) {
    return `To extract key terms from page ${currentPage}, I would analyze the text content for frequently occurring domain-specific terminology. Connect to the Claude API for full extraction capabilities.`;
  }

  if (lower.includes('annotation') || lower.includes('markup')) {
    return `You currently have ${annotationCount} annotation(s). Annotations can be highlights (yellow overlay), rectangles (red borders), or pinned notes. Click any annotation to remove it, or use the toolbar to add new ones.`;
  }

  if (lower.includes('table') || lower.includes('extract')) {
    return `Table extraction requires analyzing the page layout to identify structured data regions. You can mark table areas using the rectangle tool, then I can help parse them. Full extraction is available via the Claude API.`;
  }

  if (lower.includes('help') || lower.includes('how')) {
    return `Here's what I can help with:\n\n- **Summarize**: Get a quick overview of the current page\n- **Key Terms**: Identify important terminology\n- **Annotations**: Review and manage your markups\n- **Extract**: Pull tables and structured data\n\nUse the toolbar to highlight, draw boxes, or add notes to the PDF.`;
  }

  return `I understand you're asking about "${userMsg}". I can assist with PDF analysis, annotation management, and content extraction. For full AI capabilities, connect this assistant to a Claude API endpoint. Is there something specific about your document I can help with?`;
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
        const response = generateResponse(
          text,
          annotations.length,
          currentPage
        );
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response },
        ]);
        setIsTyping(false);
      }, 800 + Math.random() * 600);
    },
    [annotations.length, currentPage]
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
