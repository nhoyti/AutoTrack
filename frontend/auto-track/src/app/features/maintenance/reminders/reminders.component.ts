import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../core/api/api.service';

@Component({
  selector: 'app-reminders',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="reminders-page">
      <h2>PMS Reminders</h2>

      <div *ngIf="vehicleId" class="vehicle-info">
        <p>Vehicle: {{ vehicle?.make }} {{ vehicle?.model }} ({{ vehicle?.plate_number }})</p>
      </div>

      <div *ngIf="reminders && reminders.length > 0" class="reminders-list">
        <p>Total reminders: {{ reminders.length }}</p>
        <table>
          <thead>
            <tr>
              <th>Stage</th>
              <th>Scheduled For</th>
              <th>Status</th>
              <th>Generated</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let reminder of reminders">
              <td>{{ reminder.stage }}</td>
              <td>{{ reminder.scheduled_for | date:'short' }}</td>
              <td>{{ reminder.status }}</td>
              <td>{{ reminder.generated_at | date:'short' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div *ngIf="!reminders || reminders.length === 0" class="no-reminders">
        <p>No active reminders.</p>
        <p *ngIf="vehicleId">Create a service record first to generate maintenance schedules and reminders.</p>
      </div>
    </div>
  `
})
export class RemindersComponent implements OnInit {
  vehicleId!: number;
  vehicle: any = null;
  reminders: any[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    const storedVehicleId = localStorage.getItem('selectedVehicleId');
    if (storedVehicleId) {
      this.vehicleId = +storedVehicleId;
      this.loadVehicleDetails();
      this.loadReminders();
    }
  }

  loadVehicleDetails(): void {
    // Vehicle info loaded if needed
  }

  loadReminders(): void {
    this.apiService.getVehicleReminders(this.vehicleId).subscribe({
      next: (reminders: any[]) => {
        this.reminders = reminders || [];
      },
      error: (err) => {
        console.error('Failed to load reminders:', err);
        alert('Failed to load reminders');
      }
    });
  }
}