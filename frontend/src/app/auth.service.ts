import { HttpClient } from "@angular/common/http";
import { Injectable, inject, signal } from "@angular/core";
import { Observable, tap } from "rxjs";

export interface StaffUser {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: StaffUser;
}

@Injectable({ providedIn: "root" })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly tokenKey = "autotrack_access_token";
  readonly user = signal<StaffUser | null>(this.readUser());

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>("/api/auth/login", { email, password })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.tokenKey, response.access_token);
          localStorage.setItem(
            "autotrack_staff_user",
            JSON.stringify(response.user),
          );
          this.user.set(response.user);
        }),
      );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem("autotrack_staff_user");
    this.user.set(null);
  }

  isAuthenticated(): boolean {
    return localStorage.getItem(this.tokenKey) !== null;
  }

  get token(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  private readUser(): StaffUser | null {
    const storedUser = localStorage.getItem("autotrack_staff_user");
    if (!storedUser) {
      return null;
    }

    try {
      return JSON.parse(storedUser) as StaffUser;
    } catch {
      return null;
    }
  }
}
