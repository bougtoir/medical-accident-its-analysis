/**
 * STL export utility.
 * Converts a processed canvas image into a 3D relief STL file
 * suitable for slicing in Bambu Studio.
 */

export interface StlOptions {
  width: number; // physical width in mm
  height: number; // physical height in mm
  layerHeight: number; // height per layer in mm (default 0.2)
  numLayers: number; // number of layers (2-3 for single color)
  baseThickness: number; // base plate thickness in mm
}

/**
 * Generate binary STL from canvas image data.
 * Opaque pixels become raised columns; transparent pixels are empty.
 */
export function generateStl(
  imageData: ImageData,
  options: StlOptions
): ArrayBuffer {
  const { width: imgW, height: imgH, data } = imageData;
  const { width: physW, height: physH, layerHeight, numLayers, baseThickness } = options;

  const totalHeight = baseThickness + layerHeight * numLayers;
  const pixelW = physW / imgW;
  const pixelH = physH / imgH;

  // Collect all triangles
  const triangles: number[][] = [];

  for (let y = 0; y < imgH; y++) {
    for (let x = 0; x < imgW; x++) {
      const idx = (y * imgW + x) * 4;
      const alpha = data[idx + 3];

      if (alpha < 128) continue; // skip transparent pixels

      const x0 = x * pixelW;
      const x1 = (x + 1) * pixelW;
      const y0 = y * pixelH;
      const y1 = (y + 1) * pixelH;
      const z0 = 0;
      const z1 = totalHeight;

      // Top face (2 triangles)
      triangles.push([x0, y0, z1, x1, y0, z1, x1, y1, z1, 0, 0, 1]);
      triangles.push([x0, y0, z1, x1, y1, z1, x0, y1, z1, 0, 0, 1]);

      // Bottom face
      triangles.push([x0, y0, z0, x1, y1, z0, x1, y0, z0, 0, 0, -1]);
      triangles.push([x0, y0, z0, x0, y1, z0, x1, y1, z0, 0, 0, -1]);

      // Check neighbors for side faces
      if (x === 0 || data[(y * imgW + (x - 1)) * 4 + 3] < 128) {
        // Left face
        triangles.push([x0, y0, z0, x0, y0, z1, x0, y1, z1, -1, 0, 0]);
        triangles.push([x0, y0, z0, x0, y1, z1, x0, y1, z0, -1, 0, 0]);
      }
      if (x === imgW - 1 || data[(y * imgW + (x + 1)) * 4 + 3] < 128) {
        // Right face
        triangles.push([x1, y0, z0, x1, y1, z1, x1, y0, z1, 1, 0, 0]);
        triangles.push([x1, y0, z0, x1, y1, z0, x1, y1, z1, 1, 0, 0]);
      }
      if (y === 0 || data[((y - 1) * imgW + x) * 4 + 3] < 128) {
        // Front face
        triangles.push([x0, y0, z0, x1, y0, z1, x1, y0, z0, 0, -1, 0]);
        triangles.push([x0, y0, z0, x0, y0, z1, x1, y0, z1, 0, -1, 0]);
      }
      if (y === imgH - 1 || data[((y + 1) * imgW + x) * 4 + 3] < 128) {
        // Back face
        triangles.push([x0, y1, z0, x1, y1, z0, x1, y1, z1, 0, 1, 0]);
        triangles.push([x0, y1, z0, x1, y1, z1, x0, y1, z1, 0, 1, 0]);
      }
    }
  }

  // Write binary STL
  const numTriangles = triangles.length;
  const bufferSize = 84 + numTriangles * 50;
  const buffer = new ArrayBuffer(bufferSize);
  const view = new DataView(buffer);

  // Header (80 bytes)
  const header = 'Garment Printer App - STL Export';
  for (let i = 0; i < 80; i++) {
    view.setUint8(i, i < header.length ? header.charCodeAt(i) : 0);
  }

  // Number of triangles
  view.setUint32(80, numTriangles, true);

  // Write triangles
  let offset = 84;
  for (const tri of triangles) {
    // Normal (nx, ny, nz)
    view.setFloat32(offset, tri[9], true); offset += 4;
    view.setFloat32(offset, tri[10], true); offset += 4;
    view.setFloat32(offset, tri[11], true); offset += 4;
    // Vertex 1
    view.setFloat32(offset, tri[0], true); offset += 4;
    view.setFloat32(offset, tri[1], true); offset += 4;
    view.setFloat32(offset, tri[2], true); offset += 4;
    // Vertex 2
    view.setFloat32(offset, tri[3], true); offset += 4;
    view.setFloat32(offset, tri[4], true); offset += 4;
    view.setFloat32(offset, tri[5], true); offset += 4;
    // Vertex 3
    view.setFloat32(offset, tri[6], true); offset += 4;
    view.setFloat32(offset, tri[7], true); offset += 4;
    view.setFloat32(offset, tri[8], true); offset += 4;
    // Attribute byte count
    view.setUint16(offset, 0, true); offset += 2;
  }

  return buffer;
}

/**
 * Generate multi-color STL files (one per color).
 * Returns a map of hex color -> ArrayBuffer.
 */
export function generateMultiColorStl(
  imageData: ImageData,
  options: StlOptions
): Map<string, ArrayBuffer> {
  const { width: imgW, height: imgH, data } = imageData;
  const colorMap = new Map<string, ImageData>();

  // Separate image into color layers
  const colors = new Set<string>();
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] < 128) continue;
    const hex = rgbToHex(data[i], data[i + 1], data[i + 2]);
    colors.add(hex);
  }

  for (const color of colors) {
    const layerData = new ImageData(imgW, imgH);
    for (let i = 0; i < data.length; i += 4) {
      if (data[i + 3] < 128) continue;
      const hex = rgbToHex(data[i], data[i + 1], data[i + 2]);
      if (hex === color) {
        layerData.data[i] = data[i];
        layerData.data[i + 1] = data[i + 1];
        layerData.data[i + 2] = data[i + 2];
        layerData.data[i + 3] = 255;
      }
    }
    colorMap.set(color, layerData);
  }

  const result = new Map<string, ArrayBuffer>();
  for (const [color, layerImageData] of colorMap) {
    result.set(color, generateStl(layerImageData, options));
  }

  return result;
}

function rgbToHex(r: number, g: number, b: number): string {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

/**
 * Download an ArrayBuffer as a file
 */
export function downloadStl(buffer: ArrayBuffer, filename: string) {
  const blob = new Blob([buffer], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
