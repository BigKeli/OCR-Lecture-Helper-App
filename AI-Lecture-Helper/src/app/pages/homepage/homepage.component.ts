import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { AccessibleButtonComponent } from '../../shared/components/accessible-button/accessible-button.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';

// Temporary interface until models are defined
interface TemporaryLecture {
  id: string;
  title: string;
  description?: string;
  createdAt: Date;
  slideCount?: number;
}

@Component({
  selector: 'app-homepage',
  standalone: true,
  imports: [CommonModule, AccessibleButtonComponent, PageHeaderComponent],
  templateUrl: './homepage.component.html',
  styleUrls: ['./homepage.component.css']
})
export class HomepageComponent implements OnInit, OnDestroy {
  savedLectures: TemporaryLecture[] = [];
  isLoading = false;
  error: string | null = null;
  private destroy$ = new Subject<void>();

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadSavedLectures();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSavedLectures(): void {
    this.isLoading = true;
    this.error = null;
    
    // TODO: Replace with actual service call
    // this.lectureService.getSavedLectures()
    
    // Temporary mock data
    setTimeout(() => {
      this.savedLectures = [
        {
          id: '1',
          title: 'Math Lecture - Calculus',
          description: 'Introduction to derivatives and limits',
          createdAt: new Date('2024-11-15'),
          slideCount: 12
        },
        {
          id: '2',
          title: 'History - World War II',
          description: 'European theater analysis',
          createdAt: new Date('2024-11-14'),
          slideCount: 8
        }
      ];
      this.isLoading = false;
    }, 1000);
  }

  createNewLecture(): void {
    this.router.navigate(['/lecture/new']);
  }

  // Navigate to standalone camera access page
  openCamera(): void {
    this.router.navigate(['/camera']);
  }

  openLecture(lectureId: string): void {
    this.router.navigate(['/lecture', lectureId]);
  }

  deleteLecture(lecture: TemporaryLecture, event: Event): void {
    event.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${lecture.title}"?`)) {
      // TODO: Replace with actual service call
      // this.lectureService.deleteLecture(lecture.id)
      
      // Temporary implementation
      this.savedLectures = this.savedLectures.filter(l => l.id !== lecture.id);
    }
  }

  trackByLectureId(index: number, lecture: TemporaryLecture): string {
    return lecture.id;
  }

  onKeyboardNavigation(event: KeyboardEvent, action: string, lectureId?: string): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      
      switch (action) {
        case 'create':
          this.createNewLecture();
          break;
        case 'open':
          if (lectureId) this.openLecture(lectureId);
          break;
      }
    }
  }
}