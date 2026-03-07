import { useState, useCallback } from 'react';

export default function usePdf() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.2);

  const loadFile = useCallback((f) => {
    setFile(f);
    setFileName(f.name);
    setCurrentPage(1);
  }, []);

  const goToPage = useCallback(
    (page) => {
      if (page >= 1 && page <= numPages) setCurrentPage(page);
    },
    [numPages]
  );

  const zoomIn = useCallback(() => setScale((s) => Math.min(s + 0.2, 3)), []);
  const zoomOut = useCallback(
    () => setScale((s) => Math.max(s - 0.2, 0.4)),
    []
  );

  return {
    file,
    fileName,
    numPages,
    setNumPages,
    currentPage,
    goToPage,
    scale,
    zoomIn,
    zoomOut,
    loadFile,
  };
}
