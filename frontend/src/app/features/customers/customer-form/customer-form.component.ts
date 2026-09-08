import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-customer-form',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="customer-form">
      <h2>Customer Form</h2>
      <form>
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" [(ngModel)]="customer.full_name" placeholder="Full name" required />
        </div>
        <div class="form-group">
          <label>Mobile Number</label>
          <input type="tel" [(ngModel)]="customer.mobile_number" placeholder="Mobile number" />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" [(ngModel)]="customer.email" placeholder="Email" />
        </div>
        <div class="form-group">
          <label>Address</label>
          <input type="text" [(ngModel)]="customer.address" placeholder="Address" />
        </div>
        <div class="form-group">
          <label>Preferred Contact Method</label>
          <select [(ngModel)]="customer.preferred_contact_method">
            <option value="sms">SMS</option>
            <option value="email">Email</option>
            <option value="messenger">Messenger</option>
            <option value="push">Push</option>
          </select>
        </div>
        <button type="submit" class="btn-submit" (click)="onSubmit()">Save Customer</button>
      </form>
    </div>
  `,
  styles: []
})
export class CustomerFormComponent implements OnInit {
  customer: any = {
    full_name: '',
    mobile_number: '',
    email: '',
    address: '',
    preferred_contact_method: 'sms'
  };

  ngOnInit(): void {
    // TODO: Initialize form state
  }

  onSubmit(): void {
    // TODO: Submit customer form
    console.log('Customer form submitted:', this.customer);
  }
}