import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface SearchRequest {
  query: string;
  top_k: number;
}

export interface SearchResultItem {
  id: string;
  text: string;
  distance: number;
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResultItem[];
  query: string;
  total_results: number;
}

export interface UploadPhotoResponse {
  success: boolean;
  document_id: string;
  extracted_text: string;
  confidence: number;
  message: string;
  metadata: Record<string, unknown>;
}

@Injectable({
  providedIn: 'root'
})
export class Api {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  search(request: SearchRequest): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${this.baseUrl}/search`, request);
  }

  uploadPhoto(file: File): Observable<UploadPhotoResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadPhotoResponse>(`${this.baseUrl}/upload/photo`, formData);
  }
}
