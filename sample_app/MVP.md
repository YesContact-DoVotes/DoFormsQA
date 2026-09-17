# DoForms MVP Requirements Specification

## 1. Overview
DoForms is a modern web application for creating, managing, and publishing dynamic interactive web forms and collecting user responses.

## 2. Key Modules & Functional Requirements

### 2.1 Authentication & Header Navigation
- Accessible navigation bar with links: Dashboard, Form Builder, Templates, Settings.
- Quick user login modal with email and password fields.

### 2.2 Form Builder
- Input field for Form Title (required, min 3 characters).
- Input field for Form Description (optional).
- Ability to add new questions using "Add Question" button.
- Question options: Label, Type (Text, Email, Number, Dropdown), Required flag.
- Ability to delete questions.
- Ability to duplicate questions.
- "Save Form" button that persists the form state across page reloads.
- "Publish Form" button that generates a public response link.

### 2.3 Response Submission
- Public form accessible via public link or preview tab.
- Validates field constraints before submission (e.g. valid email format, non-empty required fields).
- Displays success confirmation message upon successful submission.

### 2.4 Error Handling & Persistence
- UI must prevent saving empty forms without a title.
- Form questions and titles must persist upon page reload.
- No uncaught JavaScript errors in the browser console.
