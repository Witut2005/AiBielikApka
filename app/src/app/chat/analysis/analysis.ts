import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface AnalysisData {
  status: 'brilliant' | 'great' | 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder';
  messageText: string;
  explanation: string;
}

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analysis.html',
  styleUrl: './analysis.css'
})
export class AnalysisComponent {
  @Input() data: AnalysisData | null = null;
  @Output() close = new EventEmitter<void>();

  constructor() {
    console.log('AnalysisComponent initialized');
  }

  ngOnChanges() {
    console.log('AnalysisComponent data changed:', this.data);
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      brilliant: 'Genialne!',
      great: 'Świetne!',
      best: 'Najlepsze!',
      good: 'Dobre',
      inaccuracy: 'Niedokładność',
      mistake: 'Błąd',
      blunder: 'Przeoczenie'
    };
    return labels[status] || status;
  }
}
