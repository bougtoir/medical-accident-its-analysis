import { useState, useEffect, useRef, useCallback } from 'react';
import { pixelate, floydSteinbergDither, orderedDither } from '../utils/imageProcessing';

type ProcessMode = 'pixel' | 'detail';
type DitherType = 'floyd-steinberg' | 'ordered';

interface ImageProcessorProps {
  croppedImage: string;
  onProcessed: (canvas: HTMLCanvasElement) => void;
  onBack: () => void;
}

export function ImageProcessor({ croppedImage, onProcessed, onBack }: ImageProcessorProps) {
  const [mode, setMode] = useState<ProcessMode>('pixel');
  const [pixelSize, setPixelSize] = useState(8);
  const [numColors, setNumColors] = useState(8);
  const [ditherType, setDitherType] = useState<DitherType>('floyd-steinberg');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const originalRef = useRef<ImageData | null>(null);

  const processImage = useCallback(() => {
    if (!originalRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const imgData = originalRef.current;

    let processed: ImageData;
    if (mode === 'pixel') {
      processed = pixelate(imgData, pixelSize, numColors);
    } else {
      if (ditherType === 'floyd-steinberg') {
        processed = floydSteinbergDither(imgData, numColors);
      } else {
        processed = orderedDither(imgData, numColors);
      }
    }

    canvas.width = processed.width;
    canvas.height = processed.height;
    const ctx = canvas.getContext('2d')!;
    ctx.putImageData(processed, 0, 0);
  }, [mode, pixelSize, numColors, ditherType]);

  // Load original image
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      const maxSize = mode === 'pixel' ? 200 : 400;
      let w = img.width;
      let h = img.height;
      if (w > maxSize || h > maxSize) {
        const ratio = Math.min(maxSize / w, maxSize / h);
        w = Math.round(w * ratio);
        h = Math.round(h * ratio);
      }

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = w;
      tempCanvas.height = h;
      const ctx = tempCanvas.getContext('2d')!;
      ctx.drawImage(img, 0, 0, w, h);
      originalRef.current = ctx.getImageData(0, 0, w, h);
      processImage();
    };
    img.src = croppedImage;
  }, [croppedImage, mode, processImage]);

  useEffect(() => {
    processImage();
  }, [processImage]);

  const handleConfirm = () => {
    if (canvasRef.current) {
      onProcessed(canvasRef.current);
    }
  };

  return (
    <div className="step-container">
      <h2>画像変換</h2>

      <div className="mode-selector">
        <button
          className={mode === 'pixel' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setMode('pixel')}
        >
          A: 8bit / ピクセルアート風
        </button>
        <button
          className={mode === 'detail' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setMode('detail')}
        >
          B: 高精細モード
        </button>
      </div>

      <div className="preview-area">
        <canvas ref={canvasRef} className="preview-canvas" />
      </div>

      <div className="controls">
        {mode === 'pixel' && (
          <label>
            ピクセルサイズ: {pixelSize}px
            <input
              type="range"
              min={2}
              max={24}
              step={1}
              value={pixelSize}
              onChange={(e) => setPixelSize(Number(e.target.value))}
            />
          </label>
        )}

        {mode === 'detail' && (
          <label>
            ディザリング方式
            <select
              value={ditherType}
              onChange={(e) => setDitherType(e.target.value as DitherType)}
            >
              <option value="floyd-steinberg">Floyd-Steinberg</option>
              <option value="ordered">Ordered (Bayer)</option>
            </select>
          </label>
        )}

        <label>
          色数: {numColors}
          <input
            type="range"
            min={2}
            max={16}
            step={1}
            value={numColors}
            onChange={(e) => setNumColors(Number(e.target.value))}
          />
        </label>
      </div>

      <div className="button-row">
        <button className="btn-secondary" onClick={onBack}>戻る</button>
        <button className="btn-accent" onClick={processImage}>やり直し</button>
        <button className="btn-primary" onClick={handleConfirm}>確定</button>
      </div>
    </div>
  );
}
