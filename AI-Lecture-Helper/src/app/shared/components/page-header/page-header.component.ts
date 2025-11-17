import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './page-header.component.html',
  styleUrls: ['./page-header.component.css']
})
export class PageHeaderComponent {
  @Input() title: string = '';
  @Input() showBackButton: boolean = false;
  @Input() showSettings: boolean = false;
  @Input() backRoute: string = '/';

  constructor(private router: Router) {}

  goBack(): void {
    this.router.navigate([this.backRoute]);
  }

  openSettings(): void {
    this.router.navigate(['/settings']);
  }

  openHelp(): void {
    this.router.navigate(['/help']);
  }
}