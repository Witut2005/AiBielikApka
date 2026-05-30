import { Component, Input, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-anger-chart',
  standalone: true,
  templateUrl: './anger-chart.html',
  styleUrl: './anger-chart.css'
})
export class AngerChartComponent implements OnChanges, AfterViewInit {
  @Input() data: number[] = [];
  @ViewChild('angerCanvas') angerCanvas!: ElementRef<HTMLCanvasElement>;

  private chart: Chart | null = null;

  ngAfterViewInit() {
    this.initChart();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['data'] && this.chart) {
      this.updateChart();
    }
  }

  private initChart() {
    const ctx = this.angerCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.data.map((_, i) => `Runda ${i + 1}`),
        datasets: [{
          label: 'Poziom wkurzenia Partnera',
          data: this.data,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              display: false
            }
          },
          y: {
            beginAtZero: true,
            max: 100,
            grid: {
              display: false
            },
            title: {
              display: true,
              text: 'Poziom (%)'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  private updateChart() {
    if (this.chart) {
      this.chart.data.labels = this.data.map((_, i) => `Runda ${i + 1}`);
      this.chart.data.datasets[0].data = this.data;
      this.chart.update();
    }
  }
}
