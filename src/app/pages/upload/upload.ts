import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Api, UploadPhotoResponse } from '../../services/api';

@Component({
  selector: 'app-upload',
  imports: [],
  templateUrl: './upload.html',
  styleUrl: './upload.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class Upload {
  private readonly api = inject(Api);
  
  protected readonly selectedFile = signal<File | null>(null);
  protected readonly uploadResult = signal<UploadPhotoResponse | null>(null);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly dragOver = signal(false);

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(true);
  }

  protected onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  private handleFile(file: File): void {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
      this.error.set('Invalid file type. Please upload JPG, PNG, TIFF, or BMP images.');
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      this.error.set('File size exceeds 10MB limit.');
      return;
    }

    this.selectedFile.set(file);
    this.error.set(null);
    this.uploadResult.set(null);
  }

  protected uploadFile(): void {
    const file = this.selectedFile();
    if (!file) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    this.api.uploadPhoto(file)
      .pipe(takeUntilDestroyed())
      .subscribe({
        next: (response) => {
          this.uploadResult.set(response);
          this.loading.set(false);
          this.selectedFile.set(null);
        },
        error: (err) => {
          this.error.set(err.error?.detail || 'An error occurred while uploading the file');
          this.loading.set(false);
        }
      });
  }

  protected clearSelection(): void {
    this.selectedFile.set(null);
    this.uploadResult.set(null);
    this.error.set(null);
  }
}
