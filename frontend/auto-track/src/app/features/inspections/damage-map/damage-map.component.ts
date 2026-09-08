import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface DamageItem {
  id: string;
  vehicle_area: string;
  condition_type: string;
  severity: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CRITICAL';
  isSelected: boolean;
}

@Component({
  selector: 'app-damage-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './damage-map.component.html',
  styleUrls: ['./damage-map.component.css']
})
export class DamageMapComponent {
  @Input() selectedItem: DamageItem | null = null;
  @Output() itemSelect = new EventEmitter<DamageItem>();
  @Output() itemDeselect = new EventEmitter<void>();

  damageAreas: DamageItem[] = [
    { id: 'front-bumper', vehicle_area: 'Front Bumper', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'hood', vehicle_area: 'Hood', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'left-fender', vehicle_area: 'Left Fender', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'right-fender', vehicle_area: 'Right Fender', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'door-left', vehicle_area: 'Left Door', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'door-right', vehicle_area: 'Right Door', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'roof', vehicle_area: 'Roof', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'trunk', vehicle_area: 'Trunk', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'left-side', vehicle_area: 'Left Side', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'right-side', vehicle_area: 'Right Side', condition_type: '', severity: 'MINOR', isSelected: false },
    { id: 'rear-bumper', vehicle_area: 'Rear Bumper', condition_type: '', severity: 'MINOR', isSelected: false },
  ];

  selectItem(item: DamageItem): void {
    // Deselect previously selected item
    this.damageAreas.forEach(i => i.isSelected = false);
    // Select new item
    item.isSelected = true;
    this.itemSelect.emit(item);
  }

  deselectItem(): void {
    this.damageAreas.forEach(i => i.isSelected = false);
    this.itemDeselect.emit();
  }
}