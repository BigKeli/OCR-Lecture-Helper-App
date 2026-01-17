import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { AccessibleButtonComponent } from '../../shared/components/accessible-button/accessible-button.component';
import { CameraService } from '../../core/services/camera.service';
import { CameraState, StreamConfig } from '../../core/models/camera.models';

@Component({
  selector: 'app-camera-access',
  standalone: true, // Angular standalone component
  imports: [CommonModule, PageHeaderComponent, AccessibleButtonComponent],
  templateUrl: './camera-access.component.html',
  styleUrls: ['./camera-access.component.css']
})
export class CameraAccessComponent implements OnInit, OnDestroy {
  // ViewChild decorators to access DOM elements in the template
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;

  // Camera state tracking
  cameraState: CameraState = {
    isActive: false,
    isStreaming: false,
    error: null,
    framesProcessed: 0
  };

  // Capture management
  isCapturing = false;
  capturedImages: string[] = []; // Store base64 image data

  // Subject for managing subscriptions (prevents memory leaks)
  private destroy$ = new Subject<void>();

  constructor(
    private router: Router,
    private cameraService: CameraService
  ) {}

  ngOnInit(): void {
    // Subscribe to camera state changes from the service
    this.cameraService.cameraState$
      .pipe(takeUntil(this.destroy$)) // Auto-unsubscribe on component destroy
      .subscribe(state => {
        this.cameraState = state;
      });
  }

  ngOnDestroy(): void {
    // Clean up: stop camera and complete subscriptions
    this.stopCamera();
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize camera with specific configuration
   */
  async startCamera(): Promise<void> {
    try {
      // Define camera stream configuration
      const config: StreamConfig = {
        width: 1920,        // Full HD width
        height: 1080,       // Full HD height
        frameRate: 30,      // 30 fps
        facingMode: 'user'  // Front camera (change to 'environment' for back camera)
      };

      // Request camera access from browser
      const stream = await this.cameraService.initializeCamera(config);

      // Attach stream to video element if available
      if (this.videoElement) {
        this.videoElement.nativeElement.srcObject = stream;
        await this.videoElement.nativeElement.play();
      }
    } catch (error) {
      console.error('Failed to start camera:', error);
      this.cameraState.error = 'Camera access denied or unavailable';
    }
  }

  /**
   * Stop camera and release media stream
   */
  stopCamera(): void {
    this.cameraService.stopCamera();

    // Reset video element
    if (this.videoElement) {
      this.videoElement.nativeElement.srcObject = null;
    }
  }

  /**
   * Capture single frame from video stream
   */
  captureFrame(): void {
    // Ensure video and canvas elements exist
    if (!this.videoElement || !this.canvasElement) return;

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');

    // Check if video is ready
    if (!ctx || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to base64 image data
    const imageData = canvas.toDataURL('image/jpeg', 0.9);

    // Store captured image
    this.capturedImages.unshift(imageData); // Add to beginning of array

    // Limit stored images to 10
    if (this.capturedImages.length > 10) {
      this.capturedImages = this.capturedImages.slice(0, 10);
    }

    // Visual feedback
    this.flashScreen();
  }

  /**
   * Toggle camera on/off
   */
  toggleCamera(): void {
    if (this.cameraState.isActive) {
      this.stopCamera();
    } else {
      this.startCamera();
    }
  }

  /**
   * Clear all captured images
   */
  clearCaptures(): void {
    if (confirm('Clear all captured images?')) {
      this.capturedImages = [];
    }
  }

  /**
   * Download captured image
   */
  downloadImage(imageData: string, index: number): void {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `capture-${Date.now()}-${index}.jpg`;
    link.click();
  }

  /**
   * Delete specific captured image
   */
  deleteImage(index: number): void {
    this.capturedImages.splice(index, 1);
  }

  /**
   * Navigate back to homepage
   */
  goToHome(): void {
    this.stopCamera();
    this.router.navigate(['/home']);
  }

  /**
   * Visual feedback effect when capturing
   */
  private flashScreen(): void {
    if (!this.canvasElement) return;

    const canvas = this.canvasElement.nativeElement;
    canvas.classList.add('flash');

    setTimeout(() => {
      canvas.classList.remove('flash');
    }, 200);
  }

  /**
   * TrackBy function for *ngFor optimization
   */
  trackByIndex(index: number): number {
    return index;
  }
}
