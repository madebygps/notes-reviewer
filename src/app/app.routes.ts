import { Routes } from '@angular/router';
import { Search } from './pages/search/search';
import { Upload } from './pages/upload/upload';

export const routes: Routes = [
  { path: '', component: Search },
  { path: 'upload', component: Upload },
];
