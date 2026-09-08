import { Component, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-customer-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="customer-detail">
      <h2>Customer Details</h2>
      <div *ngIf="customer" class="customer-info">
        <p><strong>Name:</strong> {{ customer.full_name }}</p>
        <p><strong>Mobile:</strong> {{ customer.mobile_number }}</p>
        <p><strong>Email:</strong> {{ customer.email }}</p>
        <p><strong>Address:</strong> {{ customer.address }}</p>
        <p><strong>Preferred Contact:</strong> {{ customer.preferred_contact_method }}</p>
        <p><strong>Status:</strong> {{ customer.status }}</p>
      </div>
      <p *ngIf="!customer">Select a customer to view details.</p>
    </div>
  `,
  styles: []
})
export class CustomerDetailComponent implements OnInit {
  @Input() customerId!: number;
  customer: any = null;

  ngOnInit(): void {
    // TODO: Load customer details from API
  }
}