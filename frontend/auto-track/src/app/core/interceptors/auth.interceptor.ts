import { inject } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export class AuthInterceptor implements HttpInterceptor {
  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<any>> {
    const authService = inject(/* AuthService */);
    const token = localStorage.getItem('autotrack_user');

    if (token) {
      const parsed = JSON.parse(token);
      const cloned = request.clone({
        setHeaders: {
          Authorization: `Bearer ${parsed?.access_token || parsed?.token || ''}`,
        },
      });
      return next.handle(cloned);
    }

    return next.handle(request);
  }
}
