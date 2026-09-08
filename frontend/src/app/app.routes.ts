import { Routes } from "@angular/router";

import { authGuard } from "./auth.guard";
import { DashboardComponent } from "./dashboard.component";
import { LoginComponent } from "./login.component";

export const routes: Routes = [
  { path: "login", component: LoginComponent },
  { path: "", component: DashboardComponent, canActivate: [authGuard] },
  { path: "**", redirectTo: "" },
];
