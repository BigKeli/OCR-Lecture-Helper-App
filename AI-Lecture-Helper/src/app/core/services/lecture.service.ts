import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, from } from 'rxjs';
import { AxiosConfigService } from '../../services/http/axios.config';
import { LectureModel } from '../models/lecture.models';
import { SlideModel } from '../models/slides.models';

@Injectable({
  providedIn: 'root'
})
export class LectureService {
  private readonly apiUrl = '/lectures';
  private lecturesSubject = new BehaviorSubject<LectureModel[]>([]);
  public lectures$ = this.lecturesSubject.asObservable();

  constructor(private axiosConfig: AxiosConfigService) {}

  // Lecture CRUD operations
  getLectures(): Observable<LectureModel[]> {
    return from(this.axiosConfig.get<LectureModel[]>(this.apiUrl));
  }

  getLectureById(lectureId: string): Observable<LectureModel> {
    return from(this.axiosConfig.get<LectureModel>(`${this.apiUrl}/${lectureId}`));
  }

  createLecture(lecture: Partial<LectureModel>): Observable<LectureModel> {
    return from(this.axiosConfig.post<LectureModel>(this.apiUrl, lecture));
  }

  updateLecture(lectureId: string, updates: Partial<LectureModel>): Observable<LectureModel> {
    return from(this.axiosConfig.put<LectureModel>(`${this.apiUrl}/${lectureId}`, updates));
  }

  deleteLecture(lectureId: string): Observable<void> {
    return from(this.axiosConfig.delete<void>(`${this.apiUrl}/${lectureId}`));
  }

  // Slide management operations
  addSlideToLecture(lectureId: string, slideData: Partial<SlideModel>): Observable<SlideModel> {
    const url = `${this.apiUrl}/${lectureId}/slides`;
    return from(this.axiosConfig.post<SlideModel>(url, slideData));
  }

  removeSlideFromLecture(lectureId: string, slideId: string): Observable<void> {
    const url = `${this.apiUrl}/${lectureId}/slides/${slideId}`;
    return from(this.axiosConfig.delete<void>(url));
  }

  updateSlide(lectureId: string, slideId: string, updates: Partial<SlideModel>): Observable<SlideModel> {
    const url = `${this.apiUrl}/${lectureId}/slides/${slideId}`;
    return from(this.axiosConfig.put<SlideModel>(url, updates));
  }

  getSlideByNumber(lectureId: string, slideNumber: number): Observable<SlideModel | null> {
    return from(this.axiosConfig.get<SlideModel>(`${this.apiUrl}/${lectureId}/slides/number/${slideNumber}`));
  }

  getSlidesForLecture(lectureId: string): Observable<SlideModel[]> {
    return from(this.axiosConfig.get<SlideModel[]>(`${this.apiUrl}/${lectureId}/slides`));
  }

  exportLectureNotes(lectureId: string, format: 'pdf' | 'txt' | 'docx'): Observable<Blob> {
    const url = `${this.apiUrl}/${lectureId}/export?format=${format}`;
    return from(this.axiosConfig.downloadFile(url));
  }

}