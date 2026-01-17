import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { CameraService } from '../../../core/services/camera.service';
import { CameraState, OCRResponse, StreamConfig } from '../../../core/models/camera.models';

// Only import components that are actually used in the template
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { AccessibleButtonComponent } from '../../../shared/components/accessible-button/accessible-button.component';

@Component({
  selector: 'app-camera',
  standalone: true,
  imports: [
    CommonModule,
    HttpClientModule,
    PageHeaderComponent,      // Used in template
    AccessibleButtonComponent // Used in template
  ],
  templateUrl: './camera.component.html',
  styleUrls: ['./camera.component.css']
})
export class CameraComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;

  lectureId: string = '';
  cameraState: CameraState = {
    isActive: false,
    isStreaming: false,
    error: null,
    framesProcessed: 0
  };
  
  ocrResults: OCRResponse[] = [];
  currentOcrText: string = '';
  isProcessing = false;
  
  private destroy$ = new Subject<void>();
  private captureInterval: any;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private cameraService: CameraService
  ) {}

  ngOnInit(): void {
    this.lectureId = this.route.snapshot.params['id'];
    
    this.cameraService.cameraState$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.cameraState = state;
      });

    this.initializeCamera();
  }

  ngOnDestroy(): void {
    this.stopCamera();
    this.destroy$.next();
    this.destroy$.complete();
  }

  async initializeCamera(): Promise<void> {
    try {
      const config: StreamConfig = {
        width: 1920,
        height: 1080,
        frameRate: 30,
        facingMode: 'environment'
      };

      const stream = await this.cameraService.initializeCamera(config);
      
      if (this.videoElement) {
        this.videoElement.nativeElement.srcObject = stream;
        this.videoElement.nativeElement.play();
      }

      this.startCapture();
    } catch (error) {
      console.error('Failed to initialize camera:', error);
    }
  }

  startCapture(): void {
    this.captureInterval = setInterval(() => {
      this.captureAndSendFrame();
    }, 2000); // Capture every 2 seconds
  }

  captureAndSendFrame(): void {
    if (!this.videoElement || !this.canvasElement || this.isProcessing) return;

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');

    if (!ctx || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob and send to Flask
    canvas.toBlob((blob) => {
      if (blob) {
        this.isProcessing = true;
        
        const frameData = {
          blob,
          timestamp: Date.now(),
          lectureId: this.lectureId
        };

        this.cameraService.sendFrameToFlask(frameData)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: (response) => {
              this.handleOcrResponse(response);
              this.isProcessing = false;
              this.cameraService.incrementFrameCount();
            },
            error: (error) => {
              console.error('OCR processing error:', error);
              this.isProcessing = false;
            }
          });
      }
    }, 'image/jpeg', 0.8);
  }

  handleOcrResponse(response: OCRResponse): void {
    if (response.success && response.text.trim()) {
      this.ocrResults.push(response);
      this.currentOcrText = response.text;
      
      // Keep only last 10 results
      if (this.ocrResults.length > 10) {
        this.ocrResults = this.ocrResults.slice(-10);
      }
    }
  }

  stopCamera(): void {
    if (this.captureInterval) {
      clearInterval(this.captureInterval);
    }
    this.cameraService.stopCamera();
  }

  goBack(): void {
    this.stopCamera();
    this.router.navigate(['/lecture', this.lectureId]);
  }

  toggleCapture(): void {
    if (this.captureInterval) {
      clearInterval(this.captureInterval);
      this.captureInterval = null;
    } else {
      this.startCapture();
    }
  }

  clearResults(): void {
    this.ocrResults = [];
    this.currentOcrText = '';
  }

  exportResults(): void {
    const allText = this.ocrResults
      .map(result => `[${new Date(result.timestamp).toLocaleTimeString()}] ${result.text}`)
      .join('\n\n');
    
    const blob = new Blob([allText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lecture-${this.lectureId}-ocr-results.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  // Add this method for template trackBy
  trackByTimestamp(index: number, result: OCRResponse): number {
    return result.timestamp;
  }
}