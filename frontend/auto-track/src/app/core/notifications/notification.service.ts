import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface NotificationPreference {
  sms_enabled: boolean;
  email_enabled: boolean;
  messenger_enabled: boolean;
  push_enabled: boolean;
  pms_reminders_enabled: boolean;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly API_URL = '/api/notifications';

  constructor(private http: HttpClient) {}

  getPreferences(customerId: number): Observable<NotificationPreference> {
    return this.http.get<NotificationPreference>(`${this.API_URL}/preferences/${customerId}`);
  }

  sendNotification(
    notification: {
      customer_id: number;
      vehicle_id: number;
      channel: 'SMS' | 'EMAIL' | 'MESSENGER_WHATSAPP';
      stage: string;
      message: string;
      recipient: string;
    }
  ): Observable<any> {
    return this.http.post(`${this.API_URL}/send`, notification);
  }

  getHistory(status?: string, customerId?: number): Observable<any> {
    let params = '';
    if (status) params += `?status=${status}`;
    if (customerId && !status) params += `?customer_id=${customerId}`;
    if (status && customerId) params += `?status=${status}&customer_id=${customerId}`;
    return this.http.get(`${this.API_URL}/history${params}`);
  }
}
