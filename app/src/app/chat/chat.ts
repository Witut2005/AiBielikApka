import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AnalysisComponent, AnalysisData } from './analysis/analysis';

interface Message {
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  status?: 'brilliant' | 'great' | 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder';
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, AnalysisComponent],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class ChatComponent {
  messages = signal<Message[]>([
    {
      text: 'Witaj! Przeanalizowałem Twoją sytuację. O czym chcesz porozmawiać najpierw?',
      sender: 'ai',
      timestamp: new Date()
    }
  ]);

  newMessage = '';
  selectedAnalysis = signal<AnalysisData | null>(null);

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
      const userMsg: Message = {
        text: this.newMessage,
        sender: 'user',
        timestamp: new Date(),
        status: this.getMockStatus()
      };
      
      this.messages.update(msgs => [...msgs, userMsg]);
      const currentInput = this.newMessage;
      this.newMessage = '';

      // Symulacja odpowiedzi AI
      setTimeout(() => {
        const aiMsg: Message = {
          text: `Dziękuję za wiadomość: "${currentInput}". Jak mogę Ci jeszcze pomóc w tej kwestii?`,
          sender: 'ai',
          timestamp: new Date()
        };
        this.messages.update(msgs => [...msgs, aiMsg]);
      }, 1000);
    }
  }
}
