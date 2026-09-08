import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../core/api/api.service';

@Component({
  selector: 'app-service-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="service-history-page">
      <h2>Service History</h2>

      <div *ngIf="vehicleId" class="vehicle-info">
        <p>Vehicle: {{ vehicle?.make }} {{ vehicle?.model }} ({{ vehicle?.plate_number }})</p>
        <p>Current Odometer: {{ vehicle?.current_odometer | odoPipe }} km</p>
      </div>

      <div *ngIf="serviceRecords && serviceRecords.length > 0" class="service-records-list">
        <p>Total service records: {{ serviceRecords.length }}</p>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Service Type</th>
              <th>Status</th>
              <th>Service Date</th>
              <th>Odometer</th>
              <th>Total Cost</th>
              <th>Completed</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let record of serviceRecords">
              <td>{{ record.id }}</td>
              <td>{{ record.service_type }}</td>
              <td>{{ record.status }}</td>
              <td>{{ record.service_date | date:'short' }}</td>
              <td>{{ record.odometer_reading | odoPipe }} km</td>
              <td>{{ record.total_cost | currency:'USD' }}</td>
              <td>{{ record.completed_at ? (record.completed | date:'short') : 'Pending' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div *ngIf="!serviceRecords || serviceRecords.length === 0" class="no-records">
        <p>No service records found for this vehicle.</p>
      </div>
    </div>
  `,
  styles: []
})
export class ServiceHistoryComponent implements OnInit {
  vehicleId!: number;
  vehicle: any = null;
  serviceRecords: any[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    const storedVehicleId = localStorage.getItem('selectedVehicleId');
    if (storedVehicleId) {
      this.vehicleId = +storedVehicleId;
      this.loadVehicleDetails();
      this.loadServiceHistory();
    }
  }

  loadVehicleDetails(): void {
    // Vehicle info loaded via API service
  }

  loadServiceHistory(): void {
    this.apiService.getServiceHistory(this.vehicleId).subscribe({
      next: (history: any) => {
        this.serviceRecords = history.items || [];
        this.vehicle = history.vehicle;
      },
      error: (err) => {
        console.error('Failed to load service history:', err);
        alert('Failed to load service history');
      }
    });
  }
}