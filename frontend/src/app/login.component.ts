import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Router } from "@angular/router";

import { AuthService } from "./auth.service";

@Component({
  selector: "app-login",
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="login-page">
      <section class="login-panel" aria-labelledby="login-title">
        <p class="eyebrow">Autohaus operations</p>
        <h1 id="login-title">Welcome back.</h1>
        <p class="lede">Sign in to continue to the staff workspace.</p>
        <form (ngSubmit)="submit()">
          <label>
            Work email
            <input
              [(ngModel)]="email"
              name="email"
              type="email"
              autocomplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              [(ngModel)]="password"
              name="password"
              type="password"
              autocomplete="current-password"
              required
            />
          </label>
          @if (error()) {
            <p class="error" role="alert">{{ error() }}</p>
          }
          <button type="submit" [disabled]="isSubmitting()">
            {{ isSubmitting() ? "Signing in..." : "Sign in" }}
          </button>
        </form>
        <p class="demo-note">
          Local development accounts use the shared demo password.
        </p>
      </section>
    </main>
  `,
  styles: [
    `
      :host {
        display: block;
        min-height: 100vh;
      }
      .login-page {
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
      }
      .login-panel {
        width: min(100%, 430px);
        padding: 42px;
        background: #fffdf9;
        border: 1px solid #e3dfd5;
      }
      .eyebrow {
        margin: 0 0 10px;
        color: #d45b45;
        font:
          0.67rem "DM Mono",
          monospace;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0 0 12px;
        color: #192735;
        font-size: 2.6rem;
        letter-spacing: -0.05em;
      }
      .lede {
        margin: 0 0 32px;
        color: #526361;
        line-height: 1.6;
      }
      form {
        display: grid;
        gap: 18px;
      }
      label {
        display: grid;
        gap: 8px;
        color: #40515b;
        font-size: 0.82rem;
        font-weight: 700;
      }
      input {
        width: 100%;
        padding: 13px 14px;
        border: 1px solid #d9d5ca;
        border-radius: 2px;
        background: #fdfbf6;
        color: #192735;
        font: inherit;
      }
      input:focus {
        outline: 2px solid #9fc2b6;
        outline-offset: 2px;
      }
      button {
        padding: 14px 18px;
        border: 0;
        border-radius: 2px;
        background: #192735;
        color: #fffdf9;
        cursor: pointer;
        font: inherit;
        font-weight: 800;
      }
      button:disabled {
        cursor: wait;
        opacity: 0.65;
      }
      .error {
        margin: 0;
        color: #b33f32;
        font-size: 0.82rem;
      }
      .demo-note {
        margin: 26px 0 0;
        color: #969188;
        font-size: 0.72rem;
        line-height: 1.5;
      }
      @media (max-width: 520px) {
        .login-panel {
          padding: 30px 24px;
        }
      }
    `,
  ],
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly error = signal("");
  readonly isSubmitting = signal(false);
  email = "";
  password = "";

  submit(): void {
    this.error.set("");
    this.isSubmitting.set(true);
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigateByUrl("/"),
      error: () => {
        this.error.set("Email or password is incorrect.");
        this.isSubmitting.set(false);
      },
    });
  }
}
