import { Routes } from '@angular/router';
import { ContextInputComponent } from './context-input/context-input';
import { ChatComponent } from './chat/chat';

export const routes: Routes = [
  { path: '', component: ContextInputComponent },
  { path: 'context', component: ContextInputComponent },
  { path: 'chat', component: ChatComponent }
];
