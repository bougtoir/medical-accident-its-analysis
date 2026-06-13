import { useRef, useEffect, useState, useCallback } from 'react';
import type { TextLayer } from './TextEditor';
import { generateStl, downloadStl, type StlOptions } from '../utils/stlExport';

type ShirtColor = '#ffffff' | '#000000' | '#1a1a2e' | '#e74c3c' | '#2ecc71';

const SHIRT_COLORS: { label: string; value: ShirtColor }[] = [
  { label: '白', value: '#ffffff' },
  { label: '黒', value: '#000000' },
  { label: 'ネイビー', value: '#1a1a2e' },
  { label: '赤', value: '#e74c3c' },
  { label: '緑', value: '#2ecc71' },
];

interface CanvasPreviewProps {
  processedImage: string;
  textLayers: TextLayer[];
  onBack: () => void;
}

const FONT_MAP: Record<string, string> = {
  pixel: '"Press Start 2P", monospace',
  mincho: '"Noto Serif JP", serif',
  gothic: '"Noto Sans JP", sans-serif',
  serif: '"Noto Serif", serif',
  sans: '"Noto Sans", sans-serif',
};

function drawDesign(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  canvasSize: number,
  textLayers: TextLayer[],
  scaleFactor = 0.8
) {
  const scale = Math.min(
    (canvasSize * scaleFactor) / img.width,
    (canvasSize * scaleFactor) / img.height
  );
  const w = img.width * scale;
  const h = img.height * scale;
  const x = (canvasSize - w) / 2;
  const y = (canvasSize - h) / 2;

  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(img, x, y, w, h);

  for (const layer of textLayers) {
    ctx.font = `${layer.size}px ${FONT_MAP[layer.font] || 'sans-serif'}`;
    ctx.fillStyle = layer.color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const tx = (layer.x / 100) * canvasSize;
    const ty = (layer.y / 100) * canvasSize;
    ctx.fillText(layer.text, tx, ty);
  }
}

export function CanvasPreview({ processedImage, textLayers, onBack }: CanvasPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [shirtColor, setShirtColor] = useState<ShirtColor>('#000000');
  const [printSize, setPrintSize] = useState(150);
  const [numLayers, setNumLayers] = useState(3);
  const [mirrored, setMirrored] = useState(false);
  const canvasSize = 400;

  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d')!;
    canvas.width = canvasSize;
    canvas.height = canvasSize;

    ctx.fillStyle = shirtColor;
    ctx.fillRect(0, 0, canvasSize, canvasSize);

    if (mirrored) {
      ctx.save();
      ctx.translate(canvasSize, 0);
      ctx.scale(-1, 1);
    }

    const img = new Image();
    img.onload = () => {
      drawDesign(ctx, img, canvasSize, textLayers);
      if (mirrored) ctx.restore();
    };
    img.src = processedImage;
  }, [shirtColor, processedImage, textLayers, mirrored]);

  useEffect(() => {
    renderCanvas();
  }, [renderCanvas]);

  const handleExportStl = () => {
    const exportCanvas = document.createElement('canvas');
    const exportSize = 100;
    exportCanvas.width = exportSize;
    exportCanvas.height = exportSize;
    const exportCtx = exportCanvas.getContext('2d')!;
    exportCtx.clearRect(0, 0, exportSize, exportSize);

    if (mirrored) {
      exportCtx.translate(exportSize, 0);
      exportCtx.scale(-1, 1);
    }

    const img = new Image();
    img.onload = () => {
      drawDesign(exportCtx, img, exportSize, textLayers);

      const imageData = exportCtx.getImageData(0, 0, exportSize, exportSize);
      const options: StlOptions = {
        width: printSize,
        height: printSize,
        layerHeight: 0.2,
        numLayers: numLayers,
        baseThickness: 0,
      };

      const stlBuffer = generateStl(imageData, options);
      downloadStl(stlBuffer, 'garment-print.stl');
    };
    img.src = processedImage;
  };

  const handleExportPng = () => {
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = canvasSize;
    exportCanvas.height = canvasSize;
    const ctx = exportCanvas.getContext('2d')!;

    ctx.fillStyle = shirtColor;
    ctx.fillRect(0, 0, canvasSize, canvasSize);

    if (mirrored) {
      ctx.translate(canvasSize, 0);
      ctx.scale(-1, 1);
    }

    const img = new Image();
    img.onload = () => {
      drawDesign(ctx, img, canvasSize, textLayers);
      const link = document.createElement('a');
      link.download = 'garment-print.png';
      link.href = exportCanvas.toDataURL('image/png');
      link.click();
    };
    img.src = processedImage;
  };

  return (
    <div className="step-container">
      <h2>プレビュー &amp; エクスポート</h2>

      <div className="shirt-color-selector">
        <span>シャツ色:</span>
        {SHIRT_COLORS.map(c => (
          <button
            key={c.value}
            className={`color-btn ${shirtColor === c.value ? 'active' : ''}`}
            style={{ backgroundColor: c.value }}
            onClick={() => setShirtColor(c.value)}
            title={c.label}
          />
        ))}
      </div>

      <div className="mirror-toggle">
        <button
          className={!mirrored ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setMirrored(false)}
        >
          ポジ（正像）
        </button>
        <button
          className={mirrored ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setMirrored(true)}
        >
          ネガ（反転・転写用）
        </button>
      </div>

      <div className="preview-area">
        <canvas ref={canvasRef} className="preview-canvas final" />
      </div>

      <div className="controls">
        <label>
          印刷サイズ: {printSize}mm × {printSize}mm
          <input
            type="range"
            min={50}
            max={300}
            step={10}
            value={printSize}
            onChange={(e) => setPrintSize(Number(e.target.value))}
          />
        </label>

        <label>
          レイヤー数: {numLayers}
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={numLayers}
            onChange={(e) => setNumLayers(Number(e.target.value))}
          />
        </label>
      </div>

      <div className="export-info">
        <p>総厚み: {(numLayers * 0.2).toFixed(1)}mm | サイズ: {printSize}mm × {printSize}mm</p>
      </div>

      <div className="button-row">
        <button className="btn-secondary" onClick={onBack}>戻る</button>
        <button className="btn-primary" onClick={handleExportStl}>
          STL ダウンロード
        </button>
        <button className="btn-accent" onClick={handleExportPng}>
          PNG ダウンロード
        </button>
      </div>
    </div>
  );
}
