import React, { useRef, useEffect, useState, useCallback } from 'react';
import AnnotationLayer from './AnnotationLayer';

export default function PdfViewer({
  file,
  currentPage,
  scale,
  onNumPages,
  annotations,
  activeTool,
  onAddAnnotation,
  onRemoveAnnotation,
}) {
  const canvasRef = useRef(null);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Load PDF document
  useEffect(() => {
    if (!file) return;

    let cancelled = false;

    const loadPdf = async () => {
      const pdfjsLib = await import('pdfjs-dist');
      pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

      const arrayBuffer = await file.arrayBuffer();
      const doc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      if (!cancelled) {
        setPdfDoc(doc);
        onNumPages(doc.numPages);
      }
    };

    loadPdf();
    return () => {
      cancelled = true;
    };
  }, [file, onNumPages]);

  // Render page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let cancelled = false;

    const renderPage = async () => {
      const page = await pdfDoc.getPage(currentPage);
      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      if (!cancelled) {
        setDimensions({ width: viewport.width, height: viewport.height });
        await page.render({ canvasContext: ctx, viewport }).promise;
      }
    };

    renderPage();
    return () => {
      cancelled = true;
    };
  }, [pdfDoc, currentPage, scale]);

  if (!file) return null;

  return (
    <div
      className="pdf-page-container"
      style={{ width: dimensions.width, height: dimensions.height }}
    >
      <canvas ref={canvasRef} />
      <AnnotationLayer
        annotations={annotations}
        activeTool={activeTool}
        onAddAnnotation={onAddAnnotation}
        onRemoveAnnotation={onRemoveAnnotation}
        containerWidth={dimensions.width}
        containerHeight={dimensions.height}
      />
    </div>
  );
}
