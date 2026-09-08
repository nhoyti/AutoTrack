import { Component } from "@angular/core";

@Component({
  selector: "at-root",
  standalone: true,
  template: `
    <div class="min-h-screen bg-gray-50 text-gray-900">
      <header class="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div class="flex items-center justify-between max-w-7xl mx-auto">
          <div class="flex items-center gap-3">
            <span class="text-xl font-bold">AutoTrack</span>
          </div>
          <div>
            <span>Staff Management System</span>
          </div>
        </div>
      </header>

      <main class="p-4">
        AutoTrack Staff Application
      </main>
    </div>
  `,
  styles: []
})
export class AppComponent {
  constructor() {}
}
