import React from 'react';

const TOOLS = [
  { id: 'highlight', icon: '\u{1F58C}', label: 'Highlight' },
  { id: 'box', icon: '\u25A1', label: 'Rectangle' },
  { id: 'note', icon: '\u{1F4CC}', label: 'Note' },
];

export default function PdfToolbar({
  fileName,
  currentPage,
  numPages,
  activeTool,
  onToolChange,
  onPageChange,
  onZoomIn,
  onZoomOut,
  onClearAnnotations,
}) {
  return (
    <div className="pdf-toolbar">
      <span className="pdf-toolbar__brand">Claude Lens</span>
      <div className="pdf-toolbar__separator" />

      {fileName && (
        <>
          <span className="pdf-toolbar__file-name" title={fileName}>
            {fileName}
          </span>
          <div className="pdf-toolbar__separator" />

          <div className="pdf-toolbar__page-nav">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              title="Previous page"
            >
              &#9664;
            </button>
            <span>
              {currentPage} / {numPages}
            </span>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= numPages}
              title="Next page"
            >
              &#9654;
            </button>
          </div>

          <div className="pdf-toolbar__separator" />

          <button
            className="pdf-toolbar__btn"
            onClick={onZoomOut}
            title="Zoom out"
          >
            &#8722;
          </button>
          <button
            className="pdf-toolbar__btn"
            onClick={onZoomIn}
            title="Zoom in"
          >
            &#43;
          </button>

          <div className="pdf-toolbar__separator" />

          <div className="pdf-toolbar__tools">
            {TOOLS.map((tool) => (
              <button
                key={tool.id}
                className={`pdf-toolbar__btn ${
                  activeTool === tool.id ? 'pdf-toolbar__btn--active' : ''
                }`}
                onClick={() =>
                  onToolChange(activeTool === tool.id ? null : tool.id)
                }
                title={tool.label}
              >
                {tool.icon}
              </button>
            ))}
            <button
              className="pdf-toolbar__btn"
              onClick={onClearAnnotations}
              title="Clear all annotations"
            >
              &#128465;
            </button>
          </div>
        </>
      )}
    </div>
  );
}
