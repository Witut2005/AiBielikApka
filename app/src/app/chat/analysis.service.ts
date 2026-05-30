import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AnalysisData } from './analysis/analysis';

export type TensionLevel = 'low' | 'medium' | 'high';

export interface AnalysisResult {
  anger_level_a: number;
  anger_level_b: number;
  signals_a: string[];
  signals_b: string[];
  overall_tension: TensionLevel;
  summary: string;
}

@Injectable({
  providedIn: 'root'
})
export class AnalysisService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:5000/api/analyze-anger';
  
  private personDescription = 'Standardowy opis osoby B';

  setContext(context: string, problem: string) {
    this.personDescription = `Opis relacji: ${context}. Aktualny problem: ${problem}`;
  }

  analyzeMessage(message: string, history: any[]): Observable<AnalysisResult> {
    const aiMessage = [...history].reverse().find(m => m.sender === 'ai')?.text || 'Brak wypowiedzi';
    const userMessage = [...history].reverse().find(m => m.sender === 'user')?.text || 'Brak wypowiedzi';

    const body = {
      text_a: userMessage,
      text_b: aiMessage,
      person_b_description: this.personDescription
    };

    return this.http.post<AnalysisResult>(this.apiUrl, body).pipe(
      map(result => {
        // Obliczamy poziom napięcia na podstawie anger_level_b
        let tension: TensionLevel = 'low';
        if (result.anger_level_b > 65) {
          tension = 'high';
        } else if (result.anger_level_b > 30) {
          tension = 'medium';
        }
        
        return {
          ...result,
          overall_tension: tension
        };
      }),
      catchError(error => {
        console.error('Błąd analizy:', error);
        // Zwracamy pusty/domyślny wynik w razie błędu, żeby nie wywalać chatu
        return of({
          anger_level_a: 0,
          anger_level_b: 0,
          signals_a: [],
          signals_b: [],
          overall_tension: 'low' as TensionLevel,
          summary: 'Nie udało się przeprowadzić analizy.'
        });
      })
    );
  }

  analyzeCommunication(message: string): Observable<AnalysisData> {
    const body = {
      message_text: message,
      context: this.personDescription
    };

    return this.http.post<any>('http://localhost:5000/api/analyze-message', body).pipe(
      map(res => ({
        ...res,
        messageText: message
      })),
      catchError(error => {
        console.error('Błąd analizy komunikacji:', error);
        return of({
          status: 'good',
          messageText: message,
          explanation: 'Nie udało się przeprowadzić szczegółowej analizy AI.',
          signals: []
        } as AnalysisData);
      })
    );
  }
}
