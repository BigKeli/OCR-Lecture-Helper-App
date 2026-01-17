import { Routes } from '@angular/router';
import { HomepageComponent } from './pages/homepage/homepage.component';
import { LectureComponent } from './pages/lecture/lecture.component';
import { CameraComponent } from './pages/lecture/camera/camera.component';
import { CameraAccessComponent } from './pages/camera-access/camera-access.component';

export const routes: Routes = [
  { path: '', redirectTo: '/home', pathMatch: 'full' },
  { path: 'home', component: HomepageComponent },
  { path: 'camera', component: CameraAccessComponent }, // Standalone camera access
  { path: 'lecture/new', component: LectureComponent },
  { path: 'lecture/:id', component: LectureComponent },
  { path: 'lecture/:id/camera', component: CameraComponent },
  { path: '**', redirectTo: '/home' }
];