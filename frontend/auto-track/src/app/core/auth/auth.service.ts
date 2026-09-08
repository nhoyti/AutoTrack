import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface StaffUser {
  id: number;
  full_name: string;
  email: string;
  role: 'ADMIN_MANAGER' | 'SERVICE_ADVISOR' | 'TECHNICIAN_PAINTER' | 'READ_ONLY';
  isAuthenticated: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private currentUserSubject = new BehaviorSubject<StaffUser | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  private readonly API_URL = '/api';

  constructor(private http: HttpClient) {
    // Try to restore user from localStorage on init
    const stored = localStorage.getItem('autotrack_user');
    if (stored) {
      this.currentUserSubject.next(JSON.parse(stored));
    }
  }

  get currentUser(): StaffUser | null {
    return this.currentUserSubject.value;
  }

  get isAuthenticated(): boolean {
    return this.currentUserSubject.value !== null;
  }

  get role(): 'ADMIN_MANAGER' | 'SERVICE_ADVISOR' | 'TECHNICIAN_PAINTER' | 'READ_ONLY' | null {
    return this.currentUser?.role ?? null;
  }

  login(credentials: { email: string; password: string }): Promise<StaffUser> {
    return this.http
      .post<StaffUser>(`${this.API_URL}/auth/login`, credentials)
      .pipe(
        map((user) => {
          localStorage.setItem('autotrack_user', JSON.stringify(user));
          this.currentUserSubject.next(user);
          return user;
        })
      )
      .toPromise();
  }

  logout(): void {
    localStorage.removeItem('autotrack_user');
    this.currentUserSubject.next(null);
  }

  refresh(): Promise<StaffUser> {
    return this.http
      .get<StaffUser>(`${this.API_URL}/auth/me`)
      .pipe(
        map((user) => {
          localStorage.setItem('autotrack_user', JSON.stringify(user));
          this.currentUserSubject.next(user);
          return user;
        })
      )
      .toPromise();
  }
}
