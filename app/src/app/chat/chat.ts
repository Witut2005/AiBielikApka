import { Component, signal, inject, ViewChild, ElementRef, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AnalysisComponent, AnalysisData } from './analysis/analysis';
import { AngerChartComponent } from './anger-chart/anger-chart';
import { AnalysisService, AnalysisResult } from './analysis.service';

interface Message {
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  status?: 'brilliant' | 'great' | 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder';
  analysis?: AnalysisResult;
  communicationAnalysis?: AnalysisData;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, AnalysisComponent, AngerChartComponent],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class ChatComponent {
  private analysisService = inject(AnalysisService);
  
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  messages = signal<Message[]>([]);
  angerLevels = signal<number[]>([50]); // Początkowy poziom wkurzenia partnera (B)
  lastAnalysis = signal<AnalysisResult | null>(null);
  isAnalyzing = signal<boolean>(false);

  newMessage = '';
  selectedAnalysis = signal<AnalysisData | null>(null);
  nextSender = signal<'user' | 'ai'>('ai');

  get placeholderText(): string {
    return this.nextSender() === 'user' ? 'Odpowiedz jako Ty...' : 'Napisz jako Druga Strona (zacznij tutaj)...';
  }

  constructor() {
    console.log('ChatComponent initialized');
    
    // Automatyczne przewijanie przy zmianie wiadomości
    effect(() => {
      this.messages(); // Subskrypcja na sygnał
      this.scrollToBottom();
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }

  private getMockStatus(): Message['status'] {
    const statuses: Message['status'][] = ['brilliant', 'great', 'best', 'good', 'inaccuracy', 'mistake', 'blunder'];
    return statuses[Math.floor(Math.random() * statuses.length)];
  }

  private getMockExplanation(status: Message['status'], text: string): string {
    const explanations: Record<string, string> = {
      brilliant: 'Twoja wypowiedź wykazała się niezwykłą empatią i zrozumieniem. To idealny sposób na deeskalację konfliktu.',
      great: 'Bardzo dobra komunikacja. Jasno wyrażasz swoje potrzeby, nie atakując przy tym partnera.',
      best: 'To była najbardziej optymalna reakcja w tej sytuacji. Precyzyjnie adresujesz sedno problemu.',
      good: 'Poprawna wypowiedź. Jest konstruktywna i prowadzi do dialogu.',
      inaccuracy: 'Wypowiedź mogłaby być nieco lepiej sformułowana. Zawiera drobne elementy, które mogą zostać odebrane jako pasywno-agresywne.',
      mistake: 'Użyte sformułowania mogą wywołać niepotrzebną defensywność. Warto unikać uogólnień typu "Ty zawsze".',
      blunder: 'Ta wypowiedź prawdopodobnie pogorszy sytuację. Skupiasz się na winie, a nie na rozwiązaniu problemu.'
    };
    return explanations[status!] || 'Brak szczegółowej analizy dla tej wypowiedzi.';
  }

  openAnalysis(msg: Message) {
    console.log('!!! CLICK DETECTED - openAnalysis CALLED !!!', msg);
    if (msg.communicationAnalysis) {
      this.selectedAnalysis.set(msg.communicationAnalysis);
      console.log('selectedAnalysis signal state (AI):', this.selectedAnalysis());
    } else if (msg.status) {
      this.selectedAnalysis.set({
        status: msg.status,
        messageText: msg.text,
        explanation: msg.analysis?.summary || this.getMockExplanation(msg.status, msg.text),
        signals: msg.sender === 'user' ? msg.analysis?.signals_a : msg.analysis?.signals_b
      });
      console.log('selectedAnalysis signal state (Mock/Tension):', this.selectedAnalysis());
    } else {
      console.warn('Message has no status, cannot open analysis');
    }
  }

  sendMessage() {
    if (this.newMessage.trim()) {
      const sender = this.nextSender();
      const text = this.newMessage;
      
      const msg: Message = {
        text: text,
        sender: sender,
        timestamp: new Date()
      };
      
      this.messages.update(msgs => [...msgs, msg]);
      this.newMessage = '';

      this.isAnalyzing.set(true);

      if (sender === 'user') {
        this.analysisService.analyzeCommunication(text).subscribe({
          next: (result) => {
            console.log('Otrzymano analizę komunikacji:', result);
            this.messages.update(msgs => {
              const lastMsg = msgs[msgs.length - 1];
              if (lastMsg && lastMsg.text === text && lastMsg.sender === 'user') {
                lastMsg.communicationAnalysis = result;
                lastMsg.status = result.status;
              }
              return [...msgs];
            });
            this.isAnalyzing.set(false);
          },
          error: (err) => {
            console.error('Błąd analizy komunikacji:', err);
            this.isAnalyzing.set(false);
          }
        });
      } else {
        // Wywołanie analizy po wiadomościach drugiej strony (ai)
        this.analysisService.analyzeMessage(text, this.messages()).subscribe({
          next: (result) => {
            console.log('Otrzymano analizę napięcia:', result);
            this.lastAnalysis.set(result);
            
            this.messages.update(msgs => {
              const lastMsg = msgs[msgs.length - 1];
              if (lastMsg && lastMsg.text === text && lastMsg.sender === 'ai') {
                lastMsg.analysis = result;
              }
              return [...msgs];
            });

            this.angerLevels.update(levels => [...levels, result.anger_level_b]);
            this.isAnalyzing.set(false);
          },
          error: (err) => {
            console.error('Błąd analizy napięcia:', err);
            this.isAnalyzing.set(false);
          }
        });
      }
      
      // Przełączamy nadawcę na następną wiadomość
      this.nextSender.set(sender === 'user' ? 'ai' : 'user');
    }
  }
}

