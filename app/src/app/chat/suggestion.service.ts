import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface Suggestion {
  percentage: number;
  text: string;
}

export interface SuggestionResult {
  insult_analysis: {
    percentage: number;
    comment: string;
  };
  my_response_analysis?: {
    percentage: number;
    comment: string;
  };
  suggestions: Suggestion[];
}

@Injectable({
  providedIn: 'root'
})
export class SuggestionService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:5000/api/analyze';

  getSuggestions(insult: string, myResponse?: string): Observable<SuggestionResult> {
    const body = {
      insult: insult,
      my_response: myResponse
    };

    return this.http.post<SuggestionResult>(this.apiUrl, body).pipe(
      catchError(error => {
        console.error('Błąd pobierania sugestii:', error);
        return of({
          insult_analysis: { percentage: 0, comment: 'Błąd połączenia z API' },
          suggestions: []
        });
      })
    );
  }
}
