import { provideExperimentalZoning } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { provideClientHydration } from '@angular/platform-browser';

export const routes: Routes = [];

export const appConfig = {
  standalone: true,
  providers: [
    provideExperimentalZoning(),
    provideRouter(routes),
    provideClientHydration(),
  ],
};
