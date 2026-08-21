# Ticket Support System - Django REST Framework

A comprehensive ticket support system built with Django and Django REST Framework (DRF). This project provides a robust API for managing customer support tickets with role-based access control.

## Features

- User Authentication: JWT-based authentication (login/register)
- Role-Based Access: Regular users, Support staff, Admins
- Ticket Management: Create, view, update, and delete tickets
- Ticket Responses: Users and support staff can reply to tickets
- Status Management: Support staff can change ticket status (open, in_progress, closed)
- Search & Filter: Search tickets by title/description, filter by status
- Admin Panel: Django admin interface for full management

## Technology Stack

- Python 3.8+
- Django 6.0.6
- Django REST Framework 3.15.2
- Simple JWT for authentication
- SQLite (default), can be switched to PostgreSQL/MySQL

## Installation

### 1. Clone the repository
`bash
git clone https://github.com/abolfazlhashemiorg/ticket_system
cd ticket_system