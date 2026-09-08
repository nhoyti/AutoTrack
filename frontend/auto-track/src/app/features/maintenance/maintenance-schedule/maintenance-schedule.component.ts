import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../core/api/api.service';

@Component({
  selector: 'app-maintenance-schedule',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="maintenance-schedule-page">
      <h2>Maintenance Schedule</h2>

      <div *ngIf="vehicleId" class="vehicle-info">
        <p>Vehicle: {{ vehicle?.make }} {{ vehicle?.model }} ({{ vehicle?.plate_number }})</p>
      </div>

      <div *ngIf="schedules && schedules.length > 0" class="schedules-list">
        <p>Total schedules: {{ schedules.length }}</p>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Due Date</th>
              <th>Due Odometer</th>
              <th>Status</th>
              <th>Created</th>
              <th>Completed</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let schedule of schedules">
              <td>{{ schedule.maintenance_type }}</td>
              <td>{{ schedule.due_date | date:'short' }}</td>
              <td>{{ schedule.due_odometer | odoPipe }} km</td>
              <td>{{ schedule.status }}</td>
              <td>{{ schedule.created_at | date:'short' }}</td>
              <td>{{ schedule.completed_at ? (schedule.completed | date:'short') : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div *ngIf="!schedules || schedules.length === 0" class="no-schedules">
        <p>No maintenance schedules found.</p>
        <p *ngIf="vehicleId">Create a service record first to generate schedules.</p>
      </div>
    </div>
  `,
  styles: []
})
export class MaintenanceScheduleComponent implements OnInit {
  vehicleId!: number;
  vehicle: any = null;
  schedules: any[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    const storedVehicleId = localStorage.getItem('selectedVehicleId');
    if (storedVehicleId) {
      this.vehicleId = +storedVehicleId;
      this.loadVehicleDetails();
      this.loadSchedules();
    }
  }

  loadVehicleDetails(): void {
    // Vehicle info can be loaded if needed
  }

  loadSchedules(): void {
    this.apiService.getVehicleSchedule(this.vehicleId).subscribe({
      next: (schedules: any[]) => {
        this.schedules = schedules || [];
      },
      error: (err) => {
        console.error('Failed to load schedules:', err);
        alert('Failed to load maintenance schedules');
      }
    });
  }
}