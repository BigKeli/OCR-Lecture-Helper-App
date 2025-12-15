import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
// Import your custom components
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { AccessibleButtonComponent } from '../../shared/components/accessible-button/accessible-button.component';

@Component({
  selector: 'app-lecture',
  standalone: true,
  imports: [
    CommonModule,
    PageHeaderComponent,
    AccessibleButtonComponent
  ],
  templateUrl: './lecture.component.html',
  styleUrls: ['./lecture.component.css']
})
export class LectureComponent implements OnInit, OnDestroy {
  @ViewChild('fileInput') fileInput!: ElementRef;

  lectureTitle: string = '';
  lectureSubject: string = '';
  lectureId: string = '';
  isLoading = false;
  errorMessage: string | null = null;
  loadingMessage: string = '';
  showStatus = false;
  capturedSlides = 0;

  private destroy$ = new Subject<void>();

  constructor(
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      if (params['id']) {
        this.lectureId = params['id'];
        this.loadLectureInfo(params['id']);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  goBack(): void {
    this.router.navigate(['/home']);
  }

  openCamera(): void {
    this.isLoading = true;
    this.loadingMessage = 'Initializing camera...';
    
    setTimeout(() => {
      this.isLoading = false;
      this.showStatus = true;
      // Navigate to the camera component with the lecture ID
      this.router.navigate(['/lecture', this.lectureId, 'camera']);
    }, 1500);
  }

  addLectureContent(): void {
    this.fileInput.nativeElement.click();
  }

  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    
    if (files && files.length > 0) {
      this.isLoading = true;
      this.loadingMessage = `Processing ${files.length} file(s)...`;
      
      setTimeout(() => {
        this.isLoading = false;
        this.capturedSlides += files.length;
        this.showStatus = true;
      }, 2000);
    }
  }

  viewPreviousSessions(): void {
    this.router.navigate(['/lectures/history']);
  }

  openSettings(): void {
    this.router.navigate(['/settings']);
  }

  dismissError(): void {
    this.errorMessage = null;
  }

  onKeyboardNavigation(event: KeyboardEvent, action: string): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      switch (action) {
        case 'camera':
          this.openCamera();
          break;
        case 'upload':
          this.addLectureContent();
          break;
      }
    }
  }

  private loadLectureInfo(lectureId: string): void {
    // TODO: Replace with actual service call
    this.lectureTitle = 'Math Lecture - Calculus';
    this.lectureSubject = 'Mathematics';
  }
}