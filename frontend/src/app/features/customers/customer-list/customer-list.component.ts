import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-customer-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="customer-list">
      <h2>Customers</h2>
      <input type="text" placeholder="Search by name, mobile, or email" class="search-input" />
      <ul>
        <li *ngFor="let customer of customers">{{ customer.full_name }} - {{ customer.mobile_number }}</li>
      </ul>
    </div>
  `,
  styles: []
})
export class CustomerListComponent implements OnInit {
  customers: any[] = [];

  ngOnInit(): void {
    // TODO: Load customers from API
  }
}