import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AccessibleButtonComponent } from './accessible-button.component';

describe('AccessibleButtonComponent', () => {
  let component: AccessibleButtonComponent;
  let fixture: ComponentFixture<AccessibleButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AccessibleButtonComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AccessibleButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should emit buttonClick when clicked', () => {
    spyOn(component.buttonClick, 'emit');
    
    component.buttonText = 'Test Button';
    component.onClick();
    
    expect(component.buttonClick.emit).toHaveBeenCalled();
  });

  it('should not emit when disabled', () => {
    spyOn(component.buttonClick, 'emit');
    
    component.isDisabled = true;
    component.onClick();
    
    expect(component.buttonClick.emit).not.toHaveBeenCalled();
  });

  it('should handle keyboard navigation', () => {
    spyOn(component, 'onClick');
    
    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
    const spaceEvent = new KeyboardEvent('keydown', { key: ' ' });
    
    component.onKeyDown(enterEvent);
    component.onKeyDown(spaceEvent);
    
    expect(component.onClick).toHaveBeenCalledTimes(2);
  });
});