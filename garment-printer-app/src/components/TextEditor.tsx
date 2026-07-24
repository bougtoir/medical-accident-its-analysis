import { useState } from 'react';
import { HexColorPicker } from 'react-colorful';

export interface TextLayer {
  id: string;
  text: string;
  font: string;
  color: string;
  size: number;
  x: number;
  y: number;
}

type FontOption = {
  label: string;
  value: string;
  css: string;
};

const FONT_OPTIONS: FontOption[] = [
  { label: '8bit風', value: 'pixel', css: '"Press Start 2P", monospace' },
  { label: '明朝', value: 'mincho', css: '"Noto Serif JP", serif' },
  { label: 'ゴシック', value: 'gothic', css: '"Noto Sans JP", sans-serif' },
  { label: 'Serif', value: 'serif', css: '"Noto Serif", serif' },
  { label: 'Sans-serif', value: 'sans', css: '"Noto Sans", sans-serif' },
];

interface TextEditorProps {
  textLayers: TextLayer[];
  onTextLayersChange: (layers: TextLayer[]) => void;
  onConfirm: () => void;
  onBack: () => void;
}

export function TextEditor({ textLayers, onTextLayersChange, onConfirm, onBack }: TextEditorProps) {
  const [selectedLayerId, setSelectedLayerId] = useState<string | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);

  const selectedLayer = textLayers.find(l => l.id === selectedLayerId);

  const addTextLayer = () => {
    const newLayer: TextLayer = {
      id: Date.now().toString(),
      text: 'テキスト',
      font: 'gothic',
      color: '#ffffff',
      size: 32,
      x: 50,
      y: 50,
    };
    onTextLayersChange([...textLayers, newLayer]);
    setSelectedLayerId(newLayer.id);
  };

  const updateLayer = (id: string, updates: Partial<TextLayer>) => {
    onTextLayersChange(
      textLayers.map(l => l.id === id ? { ...l, ...updates } : l)
    );
  };

  const removeLayer = (id: string) => {
    onTextLayersChange(textLayers.filter(l => l.id !== id));
    if (selectedLayerId === id) setSelectedLayerId(null);
  };

  const getFontCss = (fontValue: string): string => {
    return FONT_OPTIONS.find(f => f.value === fontValue)?.css || 'sans-serif';
  };

  return (
    <div className="step-container">
      <h2>テキスト追加</h2>

      <div className="text-layers-list">
        {textLayers.map(layer => (
          <div
            key={layer.id}
            className={`text-layer-item ${selectedLayerId === layer.id ? 'selected' : ''}`}
            onClick={() => setSelectedLayerId(layer.id)}
          >
            <span
              style={{
                fontFamily: getFontCss(layer.font),
                color: layer.color,
              }}
            >
              {layer.text || '(空)'}
            </span>
            <button
              className="btn-delete"
              onClick={(e) => { e.stopPropagation(); removeLayer(layer.id); }}
            >
              ×
            </button>
          </div>
        ))}
        <button className="btn-add" onClick={addTextLayer}>+ テキスト追加</button>
      </div>

      {selectedLayer && (
        <div className="text-editor-controls">
          <label>
            テキスト
            <input
              type="text"
              value={selectedLayer.text}
              onChange={(e) => updateLayer(selectedLayer.id, { text: e.target.value })}
              placeholder="テキストを入力"
            />
          </label>

          <label>
            フォント
            <select
              value={selectedLayer.font}
              onChange={(e) => updateLayer(selectedLayer.id, { font: e.target.value })}
            >
              {FONT_OPTIONS.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </label>

          <label>
            サイズ: {selectedLayer.size}px
            <input
              type="range"
              min={12}
              max={120}
              step={1}
              value={selectedLayer.size}
              onChange={(e) => updateLayer(selectedLayer.id, { size: Number(e.target.value) })}
            />
          </label>

          <label>
            X位置: {selectedLayer.x}%
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={selectedLayer.x}
              onChange={(e) => updateLayer(selectedLayer.id, { x: Number(e.target.value) })}
            />
          </label>

          <label>
            Y位置: {selectedLayer.y}%
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={selectedLayer.y}
              onChange={(e) => updateLayer(selectedLayer.id, { y: Number(e.target.value) })}
            />
          </label>

          <div className="color-control">
            <label>色</label>
            <div
              className="color-swatch"
              style={{ backgroundColor: selectedLayer.color }}
              onClick={() => setShowColorPicker(!showColorPicker)}
            />
            {showColorPicker && (
              <div className="color-picker-popover">
                <HexColorPicker
                  color={selectedLayer.color}
                  onChange={(color) => updateLayer(selectedLayer.id, { color })}
                />
              </div>
            )}
          </div>
        </div>
      )}

      <div className="button-row">
        <button className="btn-secondary" onClick={onBack}>戻る</button>
        <button className="btn-primary" onClick={onConfirm}>
          {textLayers.length === 0 ? 'テキストなしで進む' : '確定'}
        </button>
      </div>
    </div>
  );
}
