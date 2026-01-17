import { Slide, SlideModel } from "./slides.models";
import { User, UserModel } from "./user.models";

export interface Lecture {
  id: string;
  user: UserModel;   
  courseId: string;
  title: string;
  description?: string;
  scheduledDate: Date;
  instructor: string;
  slides: Slide[];
  status: 'scheduled' | 'ongoing' | 'completed';
  createdAt: Date;
  updatedAt: Date;
  metadata?: {
    totalSlides: number;
    totalDuration?: number; // in minutes
    captureSettings?: {
      autoCapture: boolean;
      captureInterval?: number; // in seconds
      qualityLevel: 'low' | 'medium' | 'high';
    };
  };
}

export class LectureModel implements Lecture {
  id: string;
  courseId: string;
  user: UserModel;
  title: string;
  description?: string;
  scheduledDate: Date;
  instructor: string;
  slides: SlideModel[];
  status: 'scheduled' | 'ongoing' | 'completed';
  createdAt: Date;
  updatedAt: Date;
  metadata?: {
    totalSlides: number;
    totalDuration?: number;
    captureSettings?: {
      autoCapture: boolean;
      captureInterval?: number;
      qualityLevel: 'low' | 'medium' | 'high';
    };
  };

  constructor(data: Partial<Lecture> = {}) {
    this.id = data.id || '';
    this.courseId = data.courseId || '';
    this.user = data.user || new UserModel();
    this.title = data.title || '';
    this.description = data.description;
    this.scheduledDate = data.scheduledDate || new Date();
    this.instructor = data.instructor || '';
    this.slides = (data.slides || []).map(slide => new SlideModel(slide));
    this.status = data.status || 'scheduled';
    this.createdAt = data.createdAt || new Date();
    this.updatedAt = data.updatedAt || new Date();
    this.metadata = data.metadata || {
      totalSlides: 0,
      captureSettings: {
        autoCapture: false,
        qualityLevel: 'medium'
      }
    };
  }

  addSlide(slide: SlideModel): void {
    this.slides.push(slide);
    this.metadata!.totalSlides = this.slides.length;
    this.updatedAt = new Date();
  }

  removeSlide(slideId: string): boolean {
    const index = this.slides.findIndex(slide => slide.id === slideId);
    if (index !== -1) {
      this.slides.splice(index, 1);
      this.metadata!.totalSlides = this.slides.length;
      this.updatedAt = new Date();
      return true;
    }
    return false;
  }

  getSlideByNumber(slideNumber: number): SlideModel | undefined {
    return this.slides.find(slide => slide.slideNumber === slideNumber);
  }

  startLecture(): void {
    this.status = 'ongoing';
    this.updatedAt = new Date();
  }

  endLecture(): void {
    this.status = 'completed';
    this.updatedAt = new Date();
  }
}