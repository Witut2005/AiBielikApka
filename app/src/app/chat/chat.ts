import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AnalysisComponent, AnalysisData } from './analysis/analysis';
import { AngerChartComponent } from './anger-chart/anger-chart';

interface Message {
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  status?: 'brilliant' | 'great' | 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder';
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, AnalysisComponent, AngerChartComponent],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class ChatComponent {
  messages = signal<Message[]>([]);
  angerLevels = signal<number[]>([50]); // Początkowy poziom wkurzenia

  newMessage = '';
  selectedAnalysis = signal<AnalysisData | null>(null);
  nextSender = signal<'user' | 'ai'>('ai');

  get placeholderText(): string {
    return this.nextSender() === 'user' ? 'Odpowiedz jako Ty...' : 'Napisz jako Druga Strona (zacznij tutaj)...';
  }

  constructor() {
    console.log('ChatComponent initialized');
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
    if (msg.status) {
      this.selectedAnalysis.set({
        status: msg.status,
        messageText: msg.text,
        explanation: this.getMockExplanation(msg.status, msg.text)
      });
      console.log('selectedAnalysis signal state:', this.selectedAnalysis());
    } else {
      console.warn('Message has no status, cannot open analysis');
    }
  }

  sendMessage() {
    if (this.newMessage.trim()) {
      const sender = this.nextSender();
      const msg: Message = {
        text: this.newMessage,
        sender: sender,
        timestamp: new Date(),
        status: sender === 'user' ? this.getMockStatus() : undefined
      };
      
      this.messages.update(msgs => [...msgs, msg]);
      
      // Jeśli to odpowiedź partnera (ai), aktualizujemy wykres wkurzenia
      if (sender === 'ai') {
        const currentAnger = this.angerLevels()[this.angerLevels().length - 1];
        // Losowa zmiana dla demonstracji: -20 do +20, w zakresie 0-100
        const change = Math.floor(Math.random() * 41) - 20;
        const newAnger = Math.max(0, Math.min(100, currentAnger + change));
        this.angerLevels.update(levels => [...levels, newAnger]);
      }

      this.newMessage = '';
      
      // Przełączamy nadawcę na następną wiadomość
      this.nextSender.set(sender === 'user' ? 'ai' : 'user');
    }
  }
}
