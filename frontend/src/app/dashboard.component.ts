import {
  HttpClient,
  HttpEventType,
  HttpParams,
  HttpRequest,
} from "@angular/common/http";
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Router } from "@angular/router";

import { AuthService } from "./auth.service";

interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

interface ShopConfig {
  timezone: string;
  currency: string;
  odometer_unit: string;
}

interface Customer {
  customer_id: string;
  full_name: string;
  mobile_number?: string | null;
  email?: string | null;
  preferred_contact_method: string;
  status: string;
}

interface Vehicle {
  vehicle_id: string;
  customer_id: string;
  plate_number: string;
  vin_chassis_number?: string | null;
  make?: string | null;
  model?: string | null;
  year?: number | null;
  color?: string | null;
  current_odometer: number;
  odometer_readings?: Array<{
    value: number;
    unit: string;
    source_record: string;
    is_correction?: boolean;
  }>;
}

interface Intake {
  intake_id: string;
  vehicle_id: string;
  status: string;
  notes?: string | null;
}

interface Inspection {
  inspection_id: string;
  status: string;
  concerns: Array<{ area: string; condition: string; severity: string }>;
}

@Component({
  selector: "app-dashboard",
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="app-shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">Autohaus operations</p>
          <h1>AutoTrack</h1>
        </div>
        <div class="session-actions">
          <span class="role-label">{{ user()?.role }}</span>
          <button type="button" (click)="logout()">Sign out</button>
          <div class="status-pill" [class.is-ready]="apiStatus() === 'ok'">
            <span class="status-dot"></span>
            {{ apiStatus() === "ok" ? "API connected" : "Connecting" }}
          </div>
        </div>
      </header>

      <section class="welcome-panel">
        <div>
          <p class="eyebrow">Staff workspace</p>
          <h2>Keep every vehicle moving forward.</h2>
          <p class="lede">
            The operational home for customer intake, repair work, service
            history, and return reminders.
          </p>
        </div>
        <div class="panel-mark" aria-hidden="true">AT</div>
      </section>

      <section class="section-heading">
        <div>
          <p class="eyebrow">Today</p>
          <h2>Operations overview</h2>
        </div>
        <span class="date-label">Sprint 2</span>
      </section>

      <section class="metric-grid" aria-label="Operations metrics">
        <article class="metric-card accent-coral">
          <span class="metric-label">Customers</span>
          <strong>{{ customers().length }}</strong>
          <span class="metric-note">Active client records</span>
        </article>
        <article class="metric-card accent-blue">
          <span class="metric-label">Vehicles</span>
          <strong>{{ vehicles().length }}</strong>
          <span class="metric-note">Tracked service history</span>
        </article>
        <article class="metric-card accent-gold">
          <span class="metric-label">Notifications</span><strong>--</strong
          ><span class="metric-note">Delivery health</span>
        </article>
      </section>

      <section class="foundation-grid">
        <article class="info-card">
          <div class="card-heading">
            <div>
              <p class="eyebrow">Connected foundation</p>
              <h3>System status</h3>
            </div>
            <span class="card-icon">01</span>
          </div>
          <dl>
            <div>
              <dt>Signed in as</dt>
              <dd>{{ user()?.display_name }}</dd>
            </div>
            <div>
              <dt>Service</dt>
              <dd>{{ health()?.service ?? "Waiting..." }}</dd>
            </div>
            <div>
              <dt>Environment</dt>
              <dd>{{ health()?.environment ?? "Waiting..." }}</dd>
            </div>
            <div>
              <dt>Shop timezone</dt>
              <dd>{{ config()?.timezone ?? "Waiting..." }}</dd>
            </div>
            <div>
              <dt>Odometer unit</dt>
              <dd>{{ config()?.odometer_unit ?? "Waiting..." }}</dd>
            </div>
          </dl>
        </article>

        <article class="info-card next-card">
          <div class="card-heading">
            <div>
              <p class="eyebrow">Sprint 2</p>
              <h3>Customer &amp; vehicle shell</h3>
            </div>
            <span class="card-icon">02</span>
          </div>
          <div class="mini-grid">
            <div class="mini-panel">
              <label>
                Find customer
                <input
                  [(ngModel)]="customerQuery"
                  name="customerQuery"
                  placeholder="Name, email or mobile"
                  (ngModelChange)="loadCustomers()"
                />
              </label>
              <ul class="record-list">
                @for (customer of customers(); track customer.customer_id) {
                  <li>
                    <button type="button" (click)="selectCustomer(customer)">
                      <strong>{{ customer.full_name }}</strong>
                      <span>{{
                        customer.mobile_number ?? customer.email ?? "No contact"
                      }}</span>
                    </button>
                  </li>
                }
              </ul>
            </div>

            <div class="mini-panel">
              <label>
                Find vehicle
                <input
                  [(ngModel)]="vehicleQuery"
                  name="vehicleQuery"
                  placeholder="Plate or VIN"
                  (ngModelChange)="loadVehicles()"
                />
              </label>
              <ul class="record-list">
                @for (vehicle of vehicles(); track vehicle.vehicle_id) {
                  <li>
                    <button type="button" (click)="selectVehicle(vehicle)">
                      <strong>{{ vehicle.plate_number }}</strong>
                      <span
                        >{{ vehicle.make ?? "Unknown" }}
                        {{ vehicle.model ?? "model" }}</span
                      >
                    </button>
                  </li>
                }
              </ul>
            </div>
          </div>
        </article>
      </section>

      <section class="studio-grid">
        <article class="panel-card">
          <div class="section-heading compact">
            <div>
              <p class="eyebrow">Create</p>
              <h3>Customer</h3>
            </div>
          </div>
          <form class="stacked-form" (ngSubmit)="createCustomer()">
            <label>
              Full name
              <input
                [(ngModel)]="newCustomer.full_name"
                name="customerName"
                required
              />
            </label>
            <label>
              Mobile
              <input
                [(ngModel)]="newCustomer.mobile_number"
                name="customerMobile"
              />
            </label>
            <label>
              Email
              <input
                [(ngModel)]="newCustomer.email"
                name="customerEmail"
                type="email"
              />
            </label>
            <label>
              Preferred contact
              <select
                [(ngModel)]="newCustomer.preferred_contact_method"
                name="customerPreference"
              >
                <option value="SMS">SMS</option>
                <option value="EMAIL">Email</option>
                <option value="WHATSAPP">WhatsApp</option>
                <option value="PHONE">Phone</option>
              </select>
            </label>
            <button type="submit">Save customer</button>
          </form>
        </article>

        <article class="panel-card">
          <div class="section-heading compact">
            <div>
              <p class="eyebrow">Create</p>
              <h3>Vehicle</h3>
            </div>
          </div>
          <form class="stacked-form" (ngSubmit)="createVehicle()">
            <label>
              Customer
              <select
                [(ngModel)]="newVehicle.customer_id"
                name="vehicleCustomerId"
              >
                <option value="">Select a customer</option>
                @for (customer of customers(); track customer.customer_id) {
                  <option [value]="customer.customer_id">
                    {{ customer.full_name }}
                  </option>
                }
              </select>
            </label>
            <label>
              Plate number
              <input
                [(ngModel)]="newVehicle.plate_number"
                name="vehiclePlate"
                required
              />
            </label>
            <label>
              VIN / Chassis
              <input
                [(ngModel)]="newVehicle.vin_chassis_number"
                name="vehicleVin"
              />
            </label>
            <div class="two-col">
              <label>
                Make
                <input [(ngModel)]="newVehicle.make" name="vehicleMake" />
              </label>
              <label>
                Model
                <input [(ngModel)]="newVehicle.model" name="vehicleModel" />
              </label>
            </div>
            <div class="two-col">
              <label>
                Year
                <input
                  [(ngModel)]="newVehicle.year"
                  name="vehicleYear"
                  type="number"
                />
              </label>
              <label>
                Color
                <input [(ngModel)]="newVehicle.color" name="vehicleColor" />
              </label>
            </div>
            <label>
              Current odometer
              <input
                [(ngModel)]="newVehicle.current_odometer"
                name="vehicleOdometer"
                type="number"
                min="0"
              />
            </label>
            <button type="submit">Save vehicle</button>
          </form>
        </article>
      </section>

      <section class="panel-card intake-panel">
        <div class="section-heading compact">
          <div>
            <p class="eyebrow">Sprint 3</p>
            <h3>Digital intake &amp; inspection</h3>
          </div>
          <span class="date-label">{{
            intake()?.status ?? "Not started"
          }}</span>
        </div>
        <p class="workflow-note">
          Select a vehicle above to resume its draft intake. Photos stay private
          and expire after five minutes.
        </p>
        <div class="intake-grid">
          <form class="stacked-form" (ngSubmit)="saveIntake()">
            <label>
              Selected vehicle
              <input
                [value]="selectedVehicle()?.plate_number ?? 'Choose a vehicle'"
                readonly
              />
            </label>
            <label>
              Intake notes
              <input
                [(ngModel)]="intakeNotes"
                name="intakeNotes"
                placeholder="Customer concerns or context"
              />
            </label>
            <button type="submit" [disabled]="!selectedVehicle()">
              {{ intake() ? "Resume intake" : "Start intake" }}
            </button>
          </form>
          <form class="stacked-form" (ngSubmit)="saveInspection()">
            <label
              >Vehicle area
              <input [(ngModel)]="concern.area" name="concernArea" required
            /></label>
            <label
              >Condition
              <input
                [(ngModel)]="concern.condition"
                name="concernCondition"
                required
            /></label>
            <label
              >Requested work
              <input
                [(ngModel)]="concern.requested_work"
                name="requestedWork"
                required
            /></label>
            <label
              >Severity
              <select [(ngModel)]="concern.severity" name="concernSeverity">
                <option>LOW</option>
                <option>MEDIUM</option>
                <option>HIGH</option>
                <option>CRITICAL</option>
              </select>
            </label>
            <button type="submit" [disabled]="!intake()">Save concern</button>
          </form>
        </div>
        <div class="upload-row">
          <label class="upload-control"
            >Attach photo
            <input
              type="file"
              accept="image/jpeg,image/png,image/gif"
              (change)="uploadPhoto($event)"
              [disabled]="!inspection()"
          /></label>
          @if (uploadState()) {
            <span
              >{{ uploadState()
              }}{{ uploadProgress() ? " " + uploadProgress() + "%" : "" }}</span
            >
          }
          @if (lastUpload && uploadState() === "Upload failed") {
            <button type="button" class="retry-button" (click)="retryUpload()">
              Retry
            </button>
          }
        </div>
      </section>
    </main>
  `,
  styleUrls: ["./app.component.scss"],
})
export class DashboardComponent {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly apiStatus = signal("checking");
  readonly health = signal<HealthResponse | null>(null);
  readonly config = signal<ShopConfig | null>(null);
  readonly user = this.auth.user;
  readonly customers = signal<Customer[]>([]);
  readonly vehicles = signal<Vehicle[]>([]);
  readonly selectedVehicle = signal<Vehicle | null>(null);
  readonly intake = signal<Intake | null>(null);
  readonly inspection = signal<Inspection | null>(null);
  readonly uploadState = signal("");
  readonly uploadProgress = signal(0);

  customerQuery = "";
  vehicleQuery = "";
  intakeNotes = "";
  lastUpload: File | null = null;
  concern = { area: "", condition: "", severity: "MEDIUM", requested_work: "" };
  newCustomer = {
    full_name: "",
    mobile_number: "",
    email: "",
    preferred_contact_method: "SMS",
    status: "ACTIVE",
  };
  newVehicle = {
    customer_id: "",
    plate_number: "",
    vin_chassis_number: "",
    make: "",
    model: "",
    year: 2024,
    color: "",
    current_odometer: 0,
  };

  constructor() {
    this.http.get<HealthResponse>("/health").subscribe({
      next: (response) => {
        this.health.set(response);
        this.apiStatus.set(response.status);
      },
      error: () => this.apiStatus.set("offline"),
    });
    this.http.get<ShopConfig>("/api/config/shop").subscribe({
      next: (response) => this.config.set(response),
    });
    this.loadCustomers();
    this.loadVehicles();
  }

  loadCustomers(): void {
    const params = this.customerQuery.trim()
      ? new HttpParams().set("search", this.customerQuery.trim())
      : new HttpParams();
    this.http.get<Customer[]>("/api/customers", { params }).subscribe({
      next: (response) => this.customers.set(response),
      error: () => this.customers.set([]),
    });
  }

  loadVehicles(): void {
    const params = this.vehicleQuery.trim()
      ? new HttpParams().set("search", this.vehicleQuery.trim())
      : new HttpParams();
    this.http.get<Vehicle[]>("/api/vehicles", { params }).subscribe({
      next: (response) => this.vehicles.set(response),
      error: () => this.vehicles.set([]),
    });
  }

  selectCustomer(customer: Customer): void {
    this.newVehicle.customer_id = customer.customer_id;
    this.customerQuery = customer.full_name;
    this.loadCustomers();
  }

  selectVehicle(vehicle: Vehicle): void {
    this.selectedVehicle.set(vehicle);
    this.newVehicle.customer_id = vehicle.customer_id;
    this.newVehicle.plate_number = vehicle.plate_number;
    this.newVehicle.make = vehicle.make ?? "";
    this.newVehicle.model = vehicle.model ?? "";
    this.newVehicle.color = vehicle.color ?? "";
    this.newVehicle.vin_chassis_number = vehicle.vin_chassis_number ?? "";
    this.newVehicle.current_odometer = vehicle.current_odometer;
  }

  saveIntake(): void {
    const vehicle = this.selectedVehicle();
    if (!vehicle) return;
    this.http
      .post<Intake>("/api/intakes", {
        vehicle_id: vehicle.vehicle_id,
        notes: this.intakeNotes,
      })
      .subscribe({
        next: (intake) => this.intake.set(intake),
      });
  }

  saveInspection(): void {
    const intake = this.intake();
    if (!intake) return;
    const payload = { intake_id: intake.intake_id, concerns: [this.concern] };
    this.http.post<Inspection>("/api/inspections", payload).subscribe({
      next: (inspection) => this.inspection.set(inspection),
    });
  }

  uploadPhoto(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.sendPhoto(file);
  }

  retryUpload(): void {
    if (this.lastUpload) this.sendPhoto(this.lastUpload);
  }

  private sendPhoto(file: File): void {
    const inspection = this.inspection();
    if (!inspection) return;
    this.lastUpload = file;
    this.uploadState.set("Uploading");
    this.uploadProgress.set(0);
    const form = new FormData();
    form.append("file", file);
    const request = new HttpRequest(
      "POST",
      `/api/inspections/${inspection.inspection_id}/photos`,
      form,
      { reportProgress: true },
    );
    this.http.request(request).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total)
          this.uploadProgress.set(
            Math.round((event.loaded / event.total) * 100),
          );
        if (event.type === HttpEventType.Response)
          this.uploadState.set("Photo attached");
      },
      error: () => this.uploadState.set("Upload failed"),
    });
  }

  createCustomer(): void {
    const payload = {
      full_name: this.newCustomer.full_name,
      mobile_number: this.newCustomer.mobile_number || undefined,
      email: this.newCustomer.email || undefined,
      preferred_contact_method: this.newCustomer.preferred_contact_method,
      status: this.newCustomer.status,
    };

    this.http.post<Customer>("/api/customers", payload).subscribe({
      next: (customer) => {
        const nextCustomers = [customer, ...this.customers()];
        this.customers.set(nextCustomers);
        this.newCustomer = {
          full_name: "",
          mobile_number: "",
          email: "",
          preferred_contact_method: "SMS",
          status: "ACTIVE",
        };
        this.newVehicle.customer_id = customer.customer_id;
      },
    });
  }

  createVehicle(): void {
    const payload = {
      customer_id: this.newVehicle.customer_id,
      plate_number: this.newVehicle.plate_number,
      vin_chassis_number: this.newVehicle.vin_chassis_number || undefined,
      make: this.newVehicle.make || undefined,
      model: this.newVehicle.model || undefined,
      year: this.newVehicle.year || undefined,
      color: this.newVehicle.color || undefined,
      current_odometer: Number(this.newVehicle.current_odometer ?? 0),
    };

    this.http.post<Vehicle>("/api/vehicles", payload).subscribe({
      next: (vehicle) => {
        this.vehicles.set([vehicle, ...this.vehicles()]);
        this.newVehicle = {
          customer_id: "",
          plate_number: "",
          vin_chassis_number: "",
          make: "",
          model: "",
          year: 2024,
          color: "",
          current_odometer: 0,
        };
      },
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigateByUrl("/login");
  }
}
