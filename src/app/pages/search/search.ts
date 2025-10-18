import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Api, SearchResultItem } from '../../services/api';

@Component({
  selector: 'app-search',
  imports: [ReactiveFormsModule],
  templateUrl: './search.html',
  styleUrl: './search.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class Search {
  private readonly api = inject(Api);
  
  protected readonly searchForm = new FormGroup({
    query: new FormControl('', [Validators.required, Validators.minLength(2)]),
    top_k: new FormControl(5, [Validators.required, Validators.min(1), Validators.max(50)])
  });

  protected readonly results = signal<SearchResultItem[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  protected onSubmit(): void {
    if (this.searchForm.invalid) {
      return;
    }

    const query = this.searchForm.value.query!;
    const top_k = this.searchForm.value.top_k!;

    this.loading.set(true);
    this.error.set(null);

    this.api.search({ query, top_k })
      .pipe(takeUntilDestroyed())
      .subscribe({
        next: (response) => {
          this.results.set(response.results);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail || 'An error occurred while searching');
          this.loading.set(false);
          this.results.set([]);
        }
      });
  }
}
