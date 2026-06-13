/**
 * Image processing utilities for garment printing app.
 * Handles pixelation (8-bit mode) and dithering (high-detail mode).
 */

export interface ProcessingOptions {
  mode: 'pixel' | 'detail';
  pixelSize?: number; // for pixel mode: size of each "pixel block"
  colors?: number; // number of colors to quantize to
  ditherType?: 'floyd-steinberg' | 'ordered' | 'none';
}

/**
 * Convert image data to pixelated (8-bit) style
 */
export function pixelate(
  imageData: ImageData,
  pixelSize: number,
  numColors: number
): ImageData {
  const { width, height, data } = imageData;
  const output = new ImageData(width, height);
  const outData = output.data;

  // Build color palette by quantizing
  const palette = buildPalette(imageData, numColors);

  for (let y = 0; y < height; y += pixelSize) {
    for (let x = 0; x < width; x += pixelSize) {
      // Average color in this block
      let r = 0, g = 0, b = 0, count = 0;
      for (let dy = 0; dy < pixelSize && y + dy < height; dy++) {
        for (let dx = 0; dx < pixelSize && x + dx < width; dx++) {
          const idx = ((y + dy) * width + (x + dx)) * 4;
          r += data[idx];
          g += data[idx + 1];
          b += data[idx + 2];
          count++;
        }
      }
      r = Math.round(r / count);
      g = Math.round(g / count);
      b = Math.round(b / count);

      // Find nearest palette color
      const nearest = findNearestColor([r, g, b], palette);

      // Fill block with the palette color
      for (let dy = 0; dy < pixelSize && y + dy < height; dy++) {
        for (let dx = 0; dx < pixelSize && x + dx < width; dx++) {
          const idx = ((y + dy) * width + (x + dx)) * 4;
          outData[idx] = nearest[0];
          outData[idx + 1] = nearest[1];
          outData[idx + 2] = nearest[2];
          outData[idx + 3] = 255;
        }
      }
    }
  }

  return output;
}

/**
 * Apply Floyd-Steinberg dithering for high-detail mode
 */
export function floydSteinbergDither(
  imageData: ImageData,
  numColors: number
): ImageData {
  const { width, height } = imageData;
  const output = new ImageData(width, height);
  const pixels = new Float32Array(imageData.data.length);
  for (let i = 0; i < imageData.data.length; i++) {
    pixels[i] = imageData.data[i];
  }

  const palette = buildPalette(imageData, numColors);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const oldR = Math.max(0, Math.min(255, pixels[idx]));
      const oldG = Math.max(0, Math.min(255, pixels[idx + 1]));
      const oldB = Math.max(0, Math.min(255, pixels[idx + 2]));

      const nearest = findNearestColor([oldR, oldG, oldB], palette);

      output.data[idx] = nearest[0];
      output.data[idx + 1] = nearest[1];
      output.data[idx + 2] = nearest[2];
      output.data[idx + 3] = 255;

      const errR = oldR - nearest[0];
      const errG = oldG - nearest[1];
      const errB = oldB - nearest[2];

      // Distribute error to neighbors
      distributeError(pixels, width, height, x + 1, y, errR, errG, errB, 7 / 16);
      distributeError(pixels, width, height, x - 1, y + 1, errR, errG, errB, 3 / 16);
      distributeError(pixels, width, height, x, y + 1, errR, errG, errB, 5 / 16);
      distributeError(pixels, width, height, x + 1, y + 1, errR, errG, errB, 1 / 16);
    }
  }

  return output;
}

/**
 * Apply ordered (Bayer) dithering
 */
export function orderedDither(
  imageData: ImageData,
  numColors: number
): ImageData {
  const { width, height, data } = imageData;
  const output = new ImageData(width, height);
  const palette = buildPalette(imageData, numColors);

  // 4x4 Bayer matrix
  const bayer = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
  ];
  const bayerSize = 4;
  const bayerScale = 255 / 16;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const threshold = (bayer[y % bayerSize][x % bayerSize] - 8) * bayerScale;

      const r = Math.max(0, Math.min(255, data[idx] + threshold));
      const g = Math.max(0, Math.min(255, data[idx + 1] + threshold));
      const b = Math.max(0, Math.min(255, data[idx + 2] + threshold));

      const nearest = findNearestColor([r, g, b], palette);
      output.data[idx] = nearest[0];
      output.data[idx + 1] = nearest[1];
      output.data[idx + 2] = nearest[2];
      output.data[idx + 3] = 255;
    }
  }

  return output;
}

function distributeError(
  pixels: Float32Array,
  width: number,
  height: number,
  x: number,
  y: number,
  errR: number,
  errG: number,
  errB: number,
  factor: number
) {
  if (x < 0 || x >= width || y >= height) return;
  const idx = (y * width + x) * 4;
  pixels[idx] += errR * factor;
  pixels[idx + 1] += errG * factor;
  pixels[idx + 2] += errB * factor;
}

/**
 * Build a color palette using median cut algorithm (simplified)
 */
function buildPalette(imageData: ImageData, numColors: number): number[][] {
  const { data } = imageData;
  const colors: number[][] = [];

  // Sample colors (every 4th pixel for performance)
  for (let i = 0; i < data.length; i += 16) {
    if (data[i + 3] > 128) {
      colors.push([data[i], data[i + 1], data[i + 2]]);
    }
  }

  return medianCut(colors, numColors);
}

function medianCut(colors: number[][], numColors: number): number[][] {
  if (colors.length === 0) return [[0, 0, 0]];
  if (numColors <= 1 || colors.length <= 1) {
    return [averageColors(colors)];
  }

  // Find channel with greatest range
  let maxRange = 0;
  let maxChannel = 0;
  for (let ch = 0; ch < 3; ch++) {
    const values = colors.map(c => c[ch]);
    const range = Math.max(...values) - Math.min(...values);
    if (range > maxRange) {
      maxRange = range;
      maxChannel = ch;
    }
  }

  // Sort by that channel and split
  colors.sort((a, b) => a[maxChannel] - b[maxChannel]);
  const mid = Math.floor(colors.length / 2);

  const left = medianCut(colors.slice(0, mid), Math.floor(numColors / 2));
  const right = medianCut(colors.slice(mid), Math.ceil(numColors / 2));

  return [...left, ...right];
}

function averageColors(colors: number[][]): number[] {
  if (colors.length === 0) return [0, 0, 0];
  let r = 0, g = 0, b = 0;
  for (const c of colors) {
    r += c[0];
    g += c[1];
    b += c[2];
  }
  const n = colors.length;
  return [Math.round(r / n), Math.round(g / n), Math.round(b / n)];
}

function findNearestColor(color: number[], palette: number[][]): number[] {
  let minDist = Infinity;
  let nearest = palette[0];
  for (const p of palette) {
    const dr = color[0] - p[0];
    const dg = color[1] - p[1];
    const db = color[2] - p[2];
    const dist = dr * dr + dg * dg + db * db;
    if (dist < minDist) {
      minDist = dist;
      nearest = p;
    }
  }
  return nearest;
}
