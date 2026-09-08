import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface InspectionItem {
  vehicle_area: string;
  condition_type: string;
  severity: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CRITICAL';
  requested_work: string;
  technician_notes: string;
  recommended_action: string;
}

export interface InspectionFormData {
  inspection_date: string;
  odometer_reading: number;
  overall_condition: string;
  customer_notes: string;
  items: InspectionItem[];
  draft: boolean;
}

@Component({
  selector: 'app-inspection-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './inspection-form.component.html',
  styleUrls: ['./inspection-form.component.css']
})
export class InspectionFormComponent {
  @Input() vehicleId!: number;
  @Input() inspectionDate!: string;
  @Input() odometerReading!: number;
  @Input() overallCondition!: string;
  @Input() customerNotes!: string;
  @Input() draftMode: boolean = false;
  @Output() save = new EventEmitter<InspectionFormData>();
  @Output() finalize = new EventEmitter<InspectionFormData>();

  inspectionItems: InspectionItem[] = [];
  newArea: string = '';
  newConditionType: string = '';
  newSeverity: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CRITICAL' = 'MINOR';
  newRequestedWork: string = '';
  newTechnicianNotes: string = '';
  newRecommendedAction: string = '';

  onSave(): void {
    const data: InspectionFormData = {
      inspection_date: this.inspectionDate || new Date().toISOString(),
      odometer_reading: this.odometerReading || 0,
      overall_condition: this.overallCondition || '',
      customer_notes: this.customerNotes || '',
      items: [...this.inspectionItems],
      draft: true
    };
    this.save.emit(data);
  }

  onFinalize(): void {
    const data: InspectionFormData = {
      inspection_date: this.inspectionDate || new Date().toISOString(),
      odometer_reading: this.odometerReading || 0,
      overall_condition: this.overallCondition || '',
      customer_notes: this.customerNotes || '',
      items: [...this.inspectionItems],
      draft: false
    };
    this.finalize.emit(data);
  }

  addItem(): void {
    const item: InspectionItem = {
      vehicle_area: this.newArea,
      condition_type: this.newConditionType,
      severity: this.newSeverity,
      requested_work: this.newRequestedWork,
      technician_notes: this.newTechnicianNotes,
      recommended_action: this.newRecommendedAction
    };
    this.inspectionItems.push(item);
    this.newArea = '';
    this.newConditionType = '';
    this.newSeverity = 'MINOR';
    this.newRequestedWork = '';
    this.newTechnicianNotes = '';
    this.newRecommendedAction = '';
  }

  removeItem(index: number): void {
    this.inspectionItems.splice(index, 1);
  }
}