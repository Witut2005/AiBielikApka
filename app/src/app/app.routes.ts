import { Routes } from '@angular/router';
import { ContextInputComponent } from './context-input/context-input';

export const routes: Routes = [
  { path: '', component: ContextInputComponent },
  { path: 'context', component: ContextInputComponent }
];
