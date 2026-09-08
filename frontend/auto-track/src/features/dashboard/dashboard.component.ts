import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/api/api.service';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'at-dashboard',
  standalone: true,
  template: `
    <div class="p-4">
      <h1 class="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
          <div class="text-3xl font-bold" [innerHTML]="todayVehicles"></div>
          <div class="text-sm text-gray-500 mt-2">Vehicles</div>
        </div>
        
        <div class="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
          <div class="text-3xl font-bold" [innerHTML]="inProgressJobs"></div>
          <div class="text-sm text-gray-500 mt-2">Jobs</div>
        </div>
        
        <div class="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
          <div class="text-3xl font-bold" [innerHTML]="pmsDue"></div>
          <div class="text-sm text-gray-500 mt-2">PMS Due</div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg p-6 shadow-sm mb-6">
        <h2 class="text-xl font-semibold mb-4">Today's Vehicles</h2>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Plate</th>
              <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Customer</th>
              <th class="px-6 py-3 text-left text-xs font-medium font-gray-500 uppercase tracking-wide">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr *ngFor="let vehicle of todayVehiclesList">
              <td class="px-6 py-4 whitespace-nowrap"><span class="font-medium">{{ vehicle.plate_number }}</span></td>
              <td class="px-6 py-4 whitespace-nowrap"><span class="text-sm text-gray-500">{{ vehicle.customer_name }}</span></td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span [ngClass]="statusClass(vehicle.status)" class="text-xs font-medium uppercase mr-2">
                  {{ vehicle.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="bg-white rounded-lg p-6 shadow-sm">
        <h2 class="text-xl font-semibold mb-4">Upcoming PMS</h2>
        <div class="space-y-4">
          <p *ngFor="let schedule of upcomingPMS">
            <span class="font-medium">{{ schedule.customer_name }}</span>
            <span class="ml-2 text-sm text-gray-500">{{ schedule.vehicle_plate }}</span>
            <span class="ml-2 text-sm">{{ schedule.due_label }}</span>
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [],
})
export class DashboardComponent implements OnInit {
  todayVehicles = '8';
  inProgressJobs = '5';
  pmsDue = '23';
  todayVehiclesList = [
    { plate_number: 'ABC1234', customer_name: 'Juan', status: 'Painting' },
    { plate_number: 'XYZ5678', customer_name: 'Pedro', status: 'Inspection' },
    { plate_number: 'DEF9876', customer_name: 'Maria', status: 'Ready' },
  ];
  upcomingPMS = [
    { customer_name: 'Juan', vehicle_plate: 'Fortuner', due_label: '7 days' },
    { customer_name: 'Pedro', vehicle_plate: 'Civic', due_label: '14 days' },
  ];
  currentUser: any;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
    });
    this.loadDashboardData();
  }

  private async loadDashboardData(): Promise<void> {
    try {
      // In a full implementation, we'd fetch data from the API
      // const data = await this.apiService.get<any>('/api/dashboard').toPromise();
      // this.todayVehicles = data?.today_vehicles?.toString() ?? '8';
      // this.inProgressJobs = data?.in_progress_jobs?.toString() ?? '5';
      // this.pmsDue = data?.pms_due?.toString() ?? '23';
      // this.todayVehiclesList = data?.today_vehicles_list ?? [];
      // this.upcomingPMS = data?.upcoming_pms ?? [];
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }

  statusClass(status: string): string {
    const classes: Record<string, string> = {
      Painting: 'bg-red-100 text-red-800',
      Inspection: 'bg-yellow-100 text-yellow-800',
      Ready: 'bg-green-100 text-green-800',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }
}
