import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-accessible-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './accessible-button.component.html',
  styleUrls: ['./accessible-button.component.css']
})
export class AccessibleButtonComponent {
  @Input() buttonText: string = '';
  @Input() buttonType: 'primary' | 'secondary' | 'danger' = 'primary';
  @Input() isDisabled: boolean = false;
  @Input() isLoading: boolean = false;
  @Input() ariaLabel?: string;
  @Input() ariaDescribedBy?: string;
  @Input() iconName?: string;
  @Input() isLarge: boolean = false;
  
  @Output() buttonClick = new EventEmitter<void>();

  getButtonClasses(): string {
    const classes = ['accessible-button'];
    
    classes.push(this.buttonType);
    
    if (this.isLarge) {
      classes.push('large');
    }
    
    return classes.join(' ');
  }

  onClick(): void {
    if (!this.isDisabled && !this.isLoading) {
      this.buttonClick.emit();
    }
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.onClick();
    }
  }
}