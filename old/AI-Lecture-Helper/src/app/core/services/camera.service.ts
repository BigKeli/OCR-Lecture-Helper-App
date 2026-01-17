import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { CameraState, CaptureFrame, OCRResponse, StreamConfig } from '../models/camera.models';

@Injectable({
  providedIn: 'root'
})
export class CameraService {
  private cameraStateSubject = new BehaviorSubject<CameraState>({
    isActive: false,
    isStreaming: false,
    error: null,
    framesProcessed: 0
  });

  public cameraState$ = this.cameraStateSubject.asObservable();
  private mediaStream: MediaStream | null = null;
  private captureInterval: any;

  constructor(private http: HttpClient) {}

  async initializeCamera(config: StreamConfig): Promise<MediaStream> {
    try {
      this.updateState({ isActive: true, error: null });
      
      const constraints = {
        video: {
          width: { ideal: config.width },
          height: { ideal: config.height },
          frameRate: { ideal: config.frameRate },
          facingMode: config.facingMode
        }
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.updateState({ isStreaming: true });
      
      return this.mediaStream;
    } catch (error) {
      this.updateState({ error: 'Camera access denied or not available' });
      throw error;
    }
  }

  startCapture(lectureId: string, intervalMs: number = 2000): void {
    if (!this.mediaStream) return;

    this.captureInterval = setInterval(() => {
      this.captureFrame(lectureId);
    }, intervalMs);
  }

  stopCapture(): void {
    if (this.captureInterval) {
      clearInterval(this.captureInterval);
      this.captureInterval = null;
    }
  }

  stopCamera(): void {
    this.stopCapture();
    
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    this.updateState({ 
      isActive: false, 
      isStreaming: false, 
      error: null 
    });
  }

  private captureFrame(lectureId: string): void {
    // This will be called from the component with canvas data
  }

  sendFrameToFlask(frameData: CaptureFrame): Observable<OCRResponse> {
    const formData = new FormData();
    formData.append('frame', frameData.blob);
    formData.append('lectureId', frameData.lectureId);
    formData.append('timestamp', frameData.timestamp.toString());

    return this.http.post<OCRResponse>('/api/process-frame', formData);
  }

  private updateState(updates: Partial<CameraState>): void {
    const currentState = this.cameraStateSubject.value;
    this.cameraStateSubject.next({ ...currentState, ...updates });
  }

  incrementFrameCount(): void {
    const currentState = this.cameraStateSubject.value;
    this.updateState({ framesProcessed: currentState.framesProcessed + 1 });
  }
}