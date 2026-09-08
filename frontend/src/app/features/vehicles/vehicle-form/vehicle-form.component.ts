import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-vehicle-form',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="vehicle-form">
      <h2>Vehicle Form</h2>
      <form>
        <div class="form-group">
          <label>Plate Number</label>
          <input type="text" [(ngModel)]="vehicle.plate_number" placeholder="Plate number" required />
        </div>
        <div class="form-group">
          <label>VIN/Chassis Number</label>
          <input type="text" [(ngModel)]="vehicle.vin_chassis_number" placeholder="VIN/chassis number" />
        </div>
        <div class="form-group">
          <label>Make</label>
          <input type="text" [(ngModel)]="vehicle.make" placeholder="Make" required />
        </div>
        <div class="form-group">
          <label>Model</label>
          <input type="text" [(ngModel)]="vehicle.model" placeholder="Model" required />
        </div>
        <div class="form-group">
          <label>Variant</label>
          <input type="text" [(ngModel)]="vehicle.variant" placeholder="Variant" />
        </div>
        <div class="form-group">
          <label>Year</label>
          <input type="number" [(ngModel)]="vehicle.year" placeholder="Year" required />
        </div>
        <div class="form-group">
          <label>Color</label>
          <input type="text" [(ngModel)]="vehicle.color" placeholder="Color" />
        </div>
        <div class="form-group">
          <label>Fuel Type</label>
          <input type="text" [(ngModel)]="vehicle.fuel_type" placeholder="Fuel type" />
        </div>
        <div class="form-group">
          <label>Transmission</label>
          <select [(ngModel)]="vehicle.transmission">
            <option value="">Select transmission</option>
            <option value="automatic">Automatic</option>
            <option value="manual">Manual</option>
          </select>
        </div>
        <div class="form-group">
          <label>Current Odometer</label>
          <input type="number" [(ngModel)]="vehicle.current_odometer" placeholder="Current odometer" />
        </div>
        <button type="submit" class="btn-submit" (click)="onSubmit()">Save Vehicle</button>
      </form>
    </div>
  `,
  styles: []
})
export class VehicleFormComponent implements OnInit {
  vehicle: any = {
    plate_number: '',
    vin_chassis_number: '',
    make: '',
    model: '',
    variant: '',
    year: 0,
    color: '',
    fuel_type: '',
    transmission: '',
    current_odometer: 0.0
  };

  ngOnInit(): void {
    // TODO: Initialize form state
  }

  onSubmit(): void {
    // TODO: Submit vehicle form
    console.log('Vehicle form submitted:', this.vehicle);
  }
}