import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { CustomersComponent } from './features/customers/customers.component';
import { VehiclesComponent } from './features/vehicles/vehicles.component';
import { InspectionsComponent } from './features/inspections/inspections.component';
import { PaintJobsComponent } from './features/paint-jobs/paint-jobs.component';
import { MaintenanceComponent } from './features/maintenance/maintenance.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'customers', component: CustomersComponent },
  { path: 'vehicles', component: VehiclesComponent },
  { path: 'inspections', component: InspectionsComponent },
  { path: 'paint-jobs', component: PaintJobsComponent },
  { path: 'maintenance', component: MaintenanceComponent },
  { path: '**', redirectTo: '/dashboard' },
];
