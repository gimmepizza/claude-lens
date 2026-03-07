import React, { useCallback, useRef } from 'react';
import PdfToolbar from './components/PdfToolbar';
import PdfViewer from './components/PdfViewer';
import FloatingAssistant from './components/FloatingAssistant';
import useAnnotations from './hooks/useAnnotations';
import usePdf from './hooks/usePdf';
import './styles/PdfViewer.css';
import './styles/FloatingAssistant.css';

export default function App() {
  const pdf = usePdf();
  const ann = useAnnotations();
  const fileInputRef = useRef(null);

  const handleFileDrop = useCallback(
    (e) => {
      e.preventDefault();
      const droppedFile = e.dataTransfer?.files?.[0];
      if (droppedFile && droppedFile.type === 'application/pdf') {
        pdf.loadFile(droppedFile);
      }
    },
    [pdf]
  );

  const handleFileSelect = useCallback(
    (e) => {
      const selected = e.target.files?.[0];
      if (selected) pdf.loadFile(selected);
    },
    [pdf]
  );

  return (
    <div
      className="pdf-workspace"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleFileDrop}
    >
      <PdfToolbar
        fileName={pdf.fileName}
        currentPage={pdf.currentPage}
        numPages={pdf.numPages}
        activeTool={ann.activeTool}
        onToolChange={ann.setActiveTool}
        onPageChange={pdf.goToPage}
        onZoomIn={pdf.zoomIn}
        onZoomOut={pdf.zoomOut}
        onClearAnnotations={ann.clearAnnotations}
      />

      {pdf.file ? (
        <div className="pdf-canvas-area">
          <PdfViewer
            file={pdf.file}
            currentPage={pdf.currentPage}
            scale={pdf.scale}
            onNumPages={pdf.setNumPages}
            annotations={ann.annotations}
            activeTool={ann.activeTool}
            onAddAnnotation={ann.addAnnotation}
            onRemoveAnnotation={ann.removeAnnotation}
          />
        </div>
      ) : (
        <div className="pdf-drop-zone">
          <div className="pdf-drop-zone__icon">&#128196;</div>
          <div className="pdf-drop-zone__text">
            Drop a PDF here or click to open
          </div>
          <button
            className="pdf-drop-zone__btn"
            onClick={() => fileInputRef.current?.click()}
          >
            Open PDF
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
        </div>
      )}

      <FloatingAssistant
        annotations={ann.annotations}
        currentPage={pdf.currentPage}
      />
    </div>
  );
}
