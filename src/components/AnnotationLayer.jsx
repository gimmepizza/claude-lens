import React, { useRef, useCallback, useState } from 'react';

export default function AnnotationLayer({
  annotations,
  activeTool,
  onAddAnnotation,
  onRemoveAnnotation,
  containerWidth,
  containerHeight,
}) {
  const layerRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [start, setStart] = useState(null);
  const [current, setCurrent] = useState(null);

  const getRelativePos = useCallback(
    (e) => {
      const rect = layerRef.current.getBoundingClientRect();
      return {
        x: ((e.clientX - rect.left) / rect.width) * 100,
        y: ((e.clientY - rect.top) / rect.height) * 100,
      };
    },
    []
  );

  const handleMouseDown = useCallback(
    (e) => {
      if (!activeTool) return;
      if (activeTool === 'note') {
        const pos = getRelativePos(e);
        const text = prompt('Enter note text:');
        if (text) {
          onAddAnnotation({
            type: 'note',
            x: pos.x,
            y: pos.y,
            text,
          });
        }
        return;
      }
      setDrawing(true);
      const pos = getRelativePos(e);
      setStart(pos);
      setCurrent(pos);
    },
    [activeTool, getRelativePos, onAddAnnotation]
  );

  const handleMouseMove = useCallback(
    (e) => {
      if (!drawing) return;
      setCurrent(getRelativePos(e));
    },
    [drawing, getRelativePos]
  );

  const handleMouseUp = useCallback(() => {
    if (!drawing || !start || !current) return;
    const x = Math.min(start.x, current.x);
    const y = Math.min(start.y, current.y);
    const w = Math.abs(current.x - start.x);
    const h = Math.abs(current.y - start.y);

    if (w > 1 || h > 1) {
      onAddAnnotation({
        type: activeTool === 'highlight' ? 'highlight' : 'box',
        x,
        y,
        width: w,
        height: h,
      });
    }

    setDrawing(false);
    setStart(null);
    setCurrent(null);
  }, [drawing, start, current, activeTool, onAddAnnotation]);

  const previewStyle =
    drawing && start && current
      ? {
          left: `${Math.min(start.x, current.x)}%`,
          top: `${Math.min(start.y, current.y)}%`,
          width: `${Math.abs(current.x - start.x)}%`,
          height: `${Math.abs(current.y - start.y)}%`,
        }
      : null;

  return (
    <div
      ref={layerRef}
      className={`annotation-overlay ${
        activeTool ? 'annotation-overlay--active' : ''
      } ${activeTool === 'note' ? 'annotation-overlay--text-mode' : ''}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        if (drawing) {
          setDrawing(false);
          setStart(null);
          setCurrent(null);
        }
      }}
    >
      {/* Existing annotations */}
      {annotations.map((ann) => {
        if (ann.type === 'note') {
          return (
            <div
              key={ann.id}
              className="annotation annotation--text-note"
              style={{ left: `${ann.x}%`, top: `${ann.y}%` }}
              title={ann.text}
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm(`"${ann.text}"\n\nDelete this note?`)) {
                  onRemoveAnnotation(ann.id);
                }
              }}
            >
              !
            </div>
          );
        }

        return (
          <div
            key={ann.id}
            className={`annotation annotation--${ann.type}`}
            style={{
              left: `${ann.x}%`,
              top: `${ann.y}%`,
              width: `${ann.width}%`,
              height: `${ann.height}%`,
            }}
            onClick={(e) => {
              e.stopPropagation();
              onRemoveAnnotation(ann.id);
            }}
          />
        );
      })}

      {/* Drawing preview */}
      {previewStyle && (
        <div
          className={`annotation annotation--${
            activeTool === 'highlight' ? 'highlight' : 'box'
          }`}
          style={{ ...previewStyle, opacity: 0.5 }}
        />
      )}
    </div>
  );
}
