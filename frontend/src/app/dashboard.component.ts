import { HttpClient } from "@angular/common/http";
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from "@angular/core";
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

@Component({
  selector: "app-dashboard",
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
        <span class="date-label">Foundation release</span>
      </section>

      <section class="metric-grid" aria-label="Operations metrics">
        <article class="metric-card accent-coral">
          <span class="metric-label">Active jobs</span><strong>--</strong
          ><span class="metric-note">Paint and body work</span>
        </article>
        <article class="metric-card accent-blue">
          <span class="metric-label">Upcoming PMS</span><strong>--</strong
          ><span class="metric-note">Maintenance schedules</span>
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
              <p class="eyebrow">Build sequence</p>
              <h3>Next up</h3>
            </div>
            <span class="card-icon">02</span>
          </div>
          <ol>
            <li><span>01</span> Staff authentication and roles</li>
            <li><span>02</span> Customer and vehicle records</li>
            <li><span>03</span> Intake and inspection workflow</li>
          </ol>
        </article>
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
  }

  logout(): void {
    this.auth.logout();
    this.router.navigateByUrl("/login");
  }
}
