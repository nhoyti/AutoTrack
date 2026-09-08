import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/core';
import { AuthService } from './auth.service';
import { map, take } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

  canActivate() {
    return this.auth.currentUser$.pipe(
      map((user) => {
        if (!user || !user.isAuthenticated) {
          this.router.navigate(['/']);
          return false;
        }
        return true;
      }),
      take(1)
    );
  }
}
