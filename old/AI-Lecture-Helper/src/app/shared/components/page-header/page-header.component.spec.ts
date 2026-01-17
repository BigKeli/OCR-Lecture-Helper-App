import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { PageHeaderComponent } from './page-header.component';

describe('PageHeaderComponent', () => {
  let component: PageHeaderComponent;
  let fixture: ComponentFixture<PageHeaderComponent>;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      declarations: [ PageHeaderComponent ],
      providers: [
        { provide: Router, useValue: routerSpy }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PageHeaderComponent);
    component = fixture.componentInstance;
    mockRouter = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should navigate to settings when openSettings is called', () => {
    component.openSettings();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/settings']);
  });

  it('should navigate to help when openHelp is called', () => {
    component.openHelp();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/help']);
  });

  it('should navigate back when goBack is called', () => {
    component.backRoute = '/custom-route';
    component.goBack();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/custom-route']);
  });

  it('should show back button when showBackButton is true', () => {
    component.showBackButton = true;
    fixture.detectChanges();
    
    const backButton = fixture.nativeElement.querySelector('.back-button');
    expect(backButton).toBeTruthy();
  });

  it('should hide back button when showBackButton is false', () => {
    component.showBackButton = false;
    fixture.detectChanges();
    
    const backButton = fixture.nativeElement.querySelector('.back-button');
    expect(backButton).toBeFalsy();
  });
});
