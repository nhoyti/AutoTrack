import { Component, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-vehicle-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="vehicle-detail">
      <h2>Vehicle Details</h2>
      <div *ngIf="vehicle" class="vehicle-info">
        <p><strong>Plate:</strong> {{ vehicle.plate_number }}</p>
        <p><strong>VIN/Chassis:</strong> {{ vehicle.vin_chassis_number }}</p>
        <p><strong>Make:</strong> {{ vehicle.make }}</p>
        <p><strong>Model:</strong> {{ vehicle.model }}</p>
        <p><strong>Year:</strong> {{ vehicle.year }}</p>
        <p><strong>Color:</strong> {{ vehicle.color }}</p>
        <p><strong>Fuel Type:</strong> {{ vehicle.fuel_type }}</p>
        <p><strong>Transmission:</strong> {{ vehicle.transmission }}</p>
        <p><strong>Odometer:</strong> {{ vehicle.current_odometer }}</p>
        <p><strong>Customer:</strong> {{ vehicle.customer_id }}</p>
      </div>
      <p *ngIf="!vehicle">Select a vehicle to view details.</p>
    </div>
  `,
  styles: []
})
export class VehicleDetailComponent implements OnInit {
  @Input() vehicleId!: number;
  vehicle: any = null;

  ngOnInit(): void {
    // TODO: Load vehicle details from API
  }
}