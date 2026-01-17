export interface CameraState {
    isActive: boolean;
    isStreaming: boolean;
    error: string | null;
    framesProcessed: number;
  }
  
  export interface CaptureFrame {
    blob: Blob;
    timestamp: number;
    lectureId: string;
  }
  
  export interface OCRResponse {
    text: string;
    confidence: number;
    timestamp: number;
    success: boolean;
  }
  
  export interface StreamConfig {
    width: number;
    height: number;
    frameRate: number;
    facingMode: 'user' | 'environment';
  }