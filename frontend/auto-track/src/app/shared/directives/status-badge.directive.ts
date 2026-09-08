import { Directive, Input, ElementRef, OnChanges, SimpleChanges } from '@angular/core';

export enum BadgeStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DRAFT = 'draft',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  PENDING = 'pending',
  OVERDUE = 'overdue',
  DUE_TODAY = 'due-today',
}

@Directive({
  selector: '[appStatusBadge]',
  standalone: true,
})
export class StatusBadgeDirective implements OnChanges {
  @Input('appStatusBadge') status: BadgeStatus | string = BadgeStatus.ACTIVE;
  private nativeElement: HTMLElement;

  constructor(elementRef: ElementRef) {
    this.nativeElement = elementRef.nativeElement;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['status']) {
      this.updateBadge(this.status);
    }
  }

  private updateBadge(status: string): void {
    const statuses: Record<string, string> = {
      'active': 'bg-green-100 text-green-800',
      'inactive': 'bg-gray-100 text-gray-800',
      'draft': 'bg-yellow-100 text-yellow-800',
      'completed': 'bg-green-100 text-green-800',
      'cancelled': 'bg-red-100 text-red-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'overdue': 'bg-red-100 text-red-800',
      'due-today': 'bg-orange-100 text-orange-800',
    };

    const classes = statuses[status] || statuses['active'];
    this.nativeElement.className = `inline-flex items-center rounded text-xs font-medium ${classes}`;
    this.nativeElement.setAttribute('aria-label', status);
  }
}
