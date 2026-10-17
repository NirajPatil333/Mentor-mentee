# ROSP Mentor–Mentee Collaborative Open Source Learning Platform

A full-stack web application that connects mentors and mentees for collaborative learning, mentorship, progress tracking, resource sharing, online sessions, and academic performance monitoring.

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [API Overview](#api-overview)
- [Mentor Matching Logic](#mentor-matching-logic)
- [Academic Performance and Verification](#academic-performance-and-verification)
- [Testing](#testing)
- [Security](#security)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Project Overview

The ROSP Mentor–Mentee Platform is designed to make mentorship and open-source learning more organized and accessible. It provides separate workflows for mentors and mentees, with authenticated access to features based on user roles and mentorship relationships.

Mentees can discover suitable mentors, submit mentorship requests, participate in online sessions, access learning resources, monitor progress, and manage their academic records. Mentors can manage accepted mentees, organize sessions, share resources, record progress, and review submitted certificates, achievements, and academic records.

The application uses a React frontend, Flask REST API, and MySQL database.

## Objectives

- Connect mentees with mentors based on skills, experience, ratings, and availability.
- Organize mentorship requests and online learning sessions.
- Support resource sharing and progress tracking.
- Allow mentees to manage certificates and achievements.
- Track semester-wise SGPA and calculate a simple-average CGPA.
- Allow authorized mentors to review mentee-submitted marksheets.
- Protect user data through authentication and role-based authorization.

## Features

### 1. Authentication and Authorization
- User registration and login.
- JWT-based authentication.
- Role-based access for mentors and mentees.
- Protected frontend routes and backend endpoints.

### 2. Profiles, Skills, and Interests
- Mentor and mentee profile information.
- Skill and learning-interest records.
- Mentor availability information.

### 3. Mentor Matching
- Rule-based matching using skill compatibility, experience, rating, and availability.
- Matching results help mentees discover relevant mentors.

### 4. Mentorship Requests
- Mentees can send mentorship requests.
- Mentors can review and respond to requests.
- Accepted mentorship relationships control access to relationship-specific features.

###
