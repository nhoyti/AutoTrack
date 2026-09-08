import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface InspectionPhoto {
  id: string;
  storage_path: string;
  photo_type: 'inspection' | 'paint_job' | 'other';
  caption: string;
  uploaded_by: number;
  created_at: string;
}

@Component({
  selector: 'app-photo-gallery',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './photo-gallery.component.html',
  styleUrls: ['./photo-gallery.component.css']
})
export class PhotoGalleryComponent {
  @Input() photos: InspectionPhoto[] = [];
  @Output() delete = new EventEmitter<string>();
  @Output() selectItem = new EventEmitter<string>();

  trackByPhotoId(index: number, photo: InspectionPhoto): string {
    return photo.id;
  }

  onSelect(photoId: string): void {
    this.selectItem.emit(photoId);
  }

  onDelete(photoId: string): void {
    this.delete.emit(photoId);
  }
}