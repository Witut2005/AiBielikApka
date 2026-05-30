import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AnalysisService } from '../chat/analysis.service';

@Component({
  selector: 'app-context-input',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './context-input.html',
  styleUrl: './context-input.css'
})
export class ContextInputComponent {
  private analysisService = inject(AnalysisService);
  private fb = inject(FormBuilder);
  private router = inject(Router);

  contextForm: FormGroup;

  constructor() {
    this.contextForm = this.fb.group({
      relationshipContext: ['Jesteśmy parą od 5 lat, mieszkamy razem. Ostatnio czujemy większy dystans i częściej się kłócimy o drobiazgi.', [Validators.required, Validators.minLength(10)]],
      currentProblem: ['Kłótnia o podział obowiązków domowych i brak docenienia moich starań w utrzymaniu porządku.', [Validators.required, Validators.minLength(10)]]
    });
  }

  onSubmit() {
    if (this.contextForm.valid) {
      console.log('Form Submitted:', this.contextForm.value);
      this.analysisService.setContext(
        this.contextForm.value.relationshipContext,
        this.contextForm.value.currentProblem
      );
      this.router.navigate(['/chat']);
    }
  }
}
