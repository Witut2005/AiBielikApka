import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-context-input',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './context-input.html',
  styleUrl: './context-input.css'
})
export class ContextInputComponent {
  contextForm: FormGroup;

  constructor(private fb: FormBuilder, private router: Router) {
    this.contextForm = this.fb.group({
      relationshipContext: ['', [Validators.required, Validators.minLength(10)]],
      currentProblem: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  onSubmit() {
    if (this.contextForm.valid) {
      console.log('Form Submitted:', this.contextForm.value);
      this.router.navigate(['/chat']);
    }
  }
}
