import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  password = '';

  constructor(private router: Router) {}

  onLogin() {
    if (this.email === 'admin@example.com' && this.password === 'password') {
      alert('Login Successful!');
      this.router.navigate(['/dashboard']);
    } else {
      alert('Invalid Credentials!');
    }
  }
}
