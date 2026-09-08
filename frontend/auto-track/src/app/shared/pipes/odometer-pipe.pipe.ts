import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'odometer',
  standalone: true,
})
export class OdometerPipe implements PipeTransform {
  transform(value: number | string, decimals: number = 0): string {
    const num = typeof value === 'number' ? value : Number(value);
    if (isNaN(num)) return '0';
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
}
