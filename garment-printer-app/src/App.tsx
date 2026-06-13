import { useState, useCallback } from 'react';
import { ImageCropper } from './components/ImageCropper';
import { ImageProcessor } from './components/ImageProcessor';
import { TextEditor } from './components/TextEditor';
import type { TextLayer } from './components/TextEditor';
import { CanvasPreview } from './components/CanvasPreview';
import './App.css';

type Step = 'upload' | 'crop' | 'process' | 'text' | 'preview';

function App() {
  const [step, setStep] = useState<Step>('upload');
  const [originalImage, setOriginalImage] = useState<string>('');
  const [croppedImage, setCroppedImage] = useState<string>('');
  const [processedImage, setProcessedImage] = useState<string>('');
  const [textLayers, setTextLayers] = useState<TextLayer[]>([]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setOriginalImage(reader.result as string);
      setStep('crop');
    };
    reader.readAsDataURL(file);
  }, []);

  const handleCropComplete = useCallback((cropped: string) => {
    setCroppedImage(cropped);
    setStep('process');
  }, []);

  const handleProcessed = useCallback((canvas: HTMLCanvasElement) => {
    setProcessedImage(canvas.toDataURL('image/png'));
    setStep('text');
  }, []);

  const handleTextConfirm = useCallback(() => {
    setStep('preview');
  }, []);

  const handleReset = () => {
    setStep('upload');
    setOriginalImage('');
    setCroppedImage('');
    setProcessedImage('');
    setTextLayers([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 onClick={handleReset}>Garment Printer</h1>
        <div className="step-indicator">
          {(['upload', 'crop', 'process', 'text', 'preview'] as Step[]).map((s, i) => (
            <div key={s} className={`step-dot ${step === s ? 'active' : i < ['upload', 'crop', 'process', 'text', 'preview'].indexOf(step) ? 'done' : ''}`}>
              {i + 1}
            </div>
          ))}
        </div>
      </header>

      <main className="app-main">
        {step === 'upload' && (
          <div className="step-container upload">
            <h2>写真を選択</h2>
            <p className="subtitle">印刷したい画像を選んでください</p>
            <label className="file-drop">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                capture="environment"
              />
              <div className="drop-content">
                <span className="drop-icon">📷</span>
                <span>タップして写真を選択</span>
                <span className="drop-hint">またはカメラで撮影</span>
              </div>
            </label>
          </div>
        )}

        {step === 'crop' && (
          <ImageCropper
            imageSrc={originalImage}
            onCropComplete={handleCropComplete}
            onBack={() => setStep('upload')}
          />
        )}

        {step === 'process' && (
          <ImageProcessor
            croppedImage={croppedImage}
            onProcessed={handleProcessed}
            onBack={() => setStep('crop')}
          />
        )}

        {step === 'text' && (
          <TextEditor
            textLayers={textLayers}
            onTextLayersChange={setTextLayers}
            onConfirm={handleTextConfirm}
            onBack={() => setStep('process')}
          />
        )}

        {step === 'preview' && (
          <CanvasPreview
            processedImage={processedImage}
            textLayers={textLayers}
            onBack={() => setStep('text')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
