import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../core/api/api.service';
import { VehicleService } from '../../../../core/api/vehicle.service';

@Component({
  selector: 'app-service-record',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="service-record-page">
      <h2>Service Record</h2>

      <div *ngIf="vehicleId" class="vehicle-info">
        <p>Vehicle: {{ vehicle?.make }} {{ vehicle?.model }} ({{ vehicle?.plate_number }})</p>
      </div>

      <div *ngIf="serviceRecord" class="service-record-detail">
        <p><strong>Service Type:</strong> {{ serviceRecord.service_type }}</p>
        <p><strong>Status:</strong> {{ serviceRecord.status }}</p>
        <p><strong>Service Date:</strong> {{ serviceRecord.service_date | date:'short' }}</p>
        <p><strong>Odometer:</strong> {{ serviceRecord.odometer_reading | odoPipe }} km</p>
        <p><strong>Description:</strong> {{ serviceRecord.description }}</p>
      </div>

      <div *ngIf="!serviceRecord" class="create-service">
        <h3>Create New Service Record</h3>
        <form (ngSubmit)="onCreate()" novalidate>
          <div class="form-group">
            <label>Vehicle ID</label>
            <input type="number" [(ngModel)]="vehicleId" placeholder="Vehicle ID" required />
          </div>
          <div class="form-group">
            <label>Service Type</label>
            <input type="text" [(ngModel)]="serviceType" placeholder="e.g., PMS, OIL_CHANGE" required />
          </div>
          <div class="form-group">
            <label>Service Date</label>
            <input type="date" [(ngModel)]="serviceDate" required />
          </div>
          <div class="form-group">
            <label>Odometer Reading</label>
            <input type="number" [(ngModel)]="odometerReading" placeholder="Odometer reading" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea [(ngModel)]="description" placeholder="Service description"></textarea>
          </div>
          <button type="submit" class="btn-primary">Create Service Record</button>
        </form>
      </div>
    </div>
  `,
  styles: []
})
export class ServiceRecordComponent implements OnInit {
  vehicleId!: number;
  vehicle: any = null;
  serviceType = '';
  serviceDate = '';
  odometerReading = '';
  description = '';
  serviceRecord: any = null;

  constructor(
    private apiService: ApiService,
    private vehicleService: VehicleService
  ) {}

  ngOnInit(): void {
    // Load vehicle info if vehicleId is available in localStorage or route params
    const storedVehicleId = localStorage.getItem('selectedVehicleId');
    if (storedVehicleId) {
      this.vehicleId = +storedVehicleId;
      this.loadVehicleDetails();
    }
  }

  loadVehicleDetails(): void {
    this.vehicleService.getVehicle(this.vehicleId).subscribe({
      next: (vehicle: any) => {
        this.vehicle = vehicle;
      },
      error: (err) => {
        console.error('Failed to load vehicle:', err);
      }
    });
  }

  onCreate(): void {
    this.apiService.createServiceRecord(
      this.vehicleId,
      this.serviceDate,
      this.odometerReading,
      this.serviceType,
      this.description
    ).subscribe({
      next: (record: any) => {
        this.serviceRecord = record;
        alert('Service record created successfully!');
      },
      error: (err) => {
        console.error('Failed to create service record:', err);
        alert('Failed to create service record');
      }
    });
  }
}