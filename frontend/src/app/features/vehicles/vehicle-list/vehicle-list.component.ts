import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-vehicle-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="vehicle-list">
      <h2>Vehicles</h2>
      <input type="text" placeholder="Search by plate, VIN, or customer" class="search-input" />
      <ul>
        <li *ngFor="let vehicle of vehicles">
          {{ vehicle.plate_number }} - {{ vehicle.make }} {{ vehicle.model }}
        </li>
      </ul>
    </div>
  `,
  styles: []
})
export class VehicleListComponent implements OnInit {
  vehicles: any[] = [];

  ngOnInit(): void {
    // TODO: Load vehicles from API
  }
}