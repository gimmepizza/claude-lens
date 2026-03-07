import { useState, useCallback } from 'react';

let nextId = 1;

export default function useAnnotations() {
  const [annotations, setAnnotations] = useState([]);
  const [activeTool, setActiveTool] = useState(null); // 'highlight' | 'box' | 'note' | null

  const addAnnotation = useCallback((annotation) => {
    setAnnotations((prev) => [...prev, { ...annotation, id: nextId++ }]);
  }, []);

  const removeAnnotation = useCallback((id) => {
    setAnnotations((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const clearAnnotations = useCallback(() => {
    setAnnotations([]);
  }, []);

  return {
    annotations,
    activeTool,
    setActiveTool,
    addAnnotation,
    removeAnnotation,
    clearAnnotations,
  };
}
