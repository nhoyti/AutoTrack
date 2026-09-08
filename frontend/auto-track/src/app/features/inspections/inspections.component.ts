import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
 { InspectionFormComponent } from '../inspection-form/inspection-form.component';
  { DamageMapComponent } from '../damage-map/damage-map.component';
  { PhotoGalleryComponent } from '../photo-gallery/photo-gallery.component';

@Component({
  selector: 'app-inspections',
  standalone: true,
  imports: [
    CommonModule,
    InspectionFormComponent,
    DamageMapComponent,
    PhotoGalleryComponent
  ],
  templateUrl: './inspections.component.html',
  styleUrls: ['./inspections.component.css']
})
export class InspectionsComponent {
  // Component will handle vehicle intake workflow
}