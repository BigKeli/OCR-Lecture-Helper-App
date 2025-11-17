export interface Slide {
  id: string;
  lectureId: string;
  slideNumber: number;
  capturedAt: Date;
  ocrText?: string;
  aiSummary?: string;
  aiDescription?: string;
  metadata?: {
    imageWidth: number;
    imageHeight: number;
    fileSize: number;
    mimeType: string;
    cameraSettings?: {
      brightness: number;
      contrast: number;
      resolution: string;
    };
  };
}

export class SlideModel implements Slide {
  id: string;
  lectureId: string;
  slideNumber: number;
  thumbnailUrl?: string;
  capturedAt: Date;
  ocrText?: string;
  aiSummary?: string;
  aiDescription?: string;
  metadata?: {
    imageWidth: number;
    imageHeight: number;
    fileSize: number;
    mimeType: string;
    cameraSettings?: {
      brightness: number;
      contrast: number;
      resolution: string;
    };
  };

  constructor(data: Partial<Slide> = {}) {
    this.id = data.id || '';
    this.lectureId = data.lectureId || '';
    this.slideNumber = data.slideNumber || 0;
    this.capturedAt = data.capturedAt || new Date();
    this.ocrText = data.ocrText;
    this.aiSummary = data.aiSummary;
    this.aiDescription = data.aiDescription;
    this.metadata = data.metadata;
  }

  get hasTextContent(): boolean {
    return !!(this.ocrText || this.aiSummary || this.aiDescription);
  }





  setAIResults(ocrText: string, summary: string, description: string): void {
    this.ocrText = ocrText;
    this.aiSummary = summary;
    this.aiDescription = description;
  }
}