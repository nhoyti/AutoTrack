import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/api/api.service';
import { AuthService } from '../../core/auth/auth.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'at-customers-list',
  standalone: true,
  template: `
    <div class="p-4">
      <h1 class="text-2xl font-bold mb-6">Customers</h1>
      
      <div class="mb-4">
        <input 
          type="text" 
          placeholder="Search by name, mobile, or email"
          class="border rounded px-3 py-2 w-full"
          [(ngModel)]="searchQuery"
          (ngModelChange)="onSearchChange()"
        />
      </div>
      
      <div class="mt-4">
        <button 
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Create Customer
        </button>
      </div>
      
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Name</th>
            <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Mobile</th>
            <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Vehicles</th>
            <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr *ngFor="let customer of customers$ | async">
            <td class="px-6 py-4 whitespace-nowrap"><span class="font-medium">{{ customer.full_name }}</span></td>
            <td class="px-6 py-4 whitespace-nowrap"><span class="text-sm text-gray-500">{{ customer.mobile_number }}</span></td>
            <td class="px-6 py-4 whitespace-nowrap"><span class="text-sm text-gray-500">{{ customer.email }}</span></td>
            <td class="px-6 py-4 whitespace-nowrap"><span class="text-sm text-gray-500">{{ customer.vehicle_count }}</span></td>
            <td class="px-6 py-4 whitespace-nowrap">
              <button 
                class="text-blue-600 text-sm hover:underline mr-2"
                (click)="viewCustomer(customer.id)"
              >
                View
              </button>
              <button 
                class="text-green-600 text-sm hover:underline"
                (click)="editCustomer(customer.id)"
              >
                Edit
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [],
})
export class CustomersListComponent implements OnInit {
  customers$!: Observable<any[]>;
  searchQuery = '';
  
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.loadCustomers();
  }

  private loadCustomers(): void {
    this.customers$ = this.apiService
      .get<any>('/api/customers?query=' + this.searchQuery)
      .pipe(
        map((response: any) => response?.items ?? [])
      );
  }

  onSearchChange(): void {
    this.customers$ = this.apiService
      .get<any>('/api/customers?query=' + this.searchQuery)
      .pipe(
        map((response: any) => response?.items ?? [])
      );
  }

  viewCustomer(customerId: number): void {
    // Navigate to customer detail
    console.log('View customer:', customerId);
  }

  editCustomer(customerId: number): void {
    // Navigate to customer edit
    console.log('Edit customer:', customerId);
  }
}
