# LifeCoach AI

An AI-powered life coaching web application designed to help users achieve their personal goals through intelligent conversations, journaling, and goal tracking.

## Features

- **AI Chat**: Engage in meaningful conversations with an AI life coach
- **AI Journal**: Maintain a digital journal with AI-powered insights
- **Goal Tracking**: Set and track personal goals with progress monitoring
- **User Authentication**: Secure user accounts and data management
- **Premium Features**: Access to advanced AI analysis and personalized plans (coming soon)
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Technology Stack

### Backend
- **FastAPI**: High-performance web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping
- **SQLite**: Lightweight database for data storage
- **JWT**: JSON Web Tokens for authentication
- **Stripe**: Payment processing for premium features

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with responsive design
- **Vanilla JavaScript**: Client-side functionality without frameworks

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd lifecoach-ai-web-sites
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `backend/.env.example` to `backend/.env`
   - Fill in your configuration values (API keys, database URLs, etc.)

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Open your browser:**
   Navigate to `http://127.0.0.1:8000`

## Usage

1. **Sign Up/Login**: Create an account or log in to access your personalized dashboard
2. **AI Chat**: Start conversations with the AI life coach for guidance and advice
3. **Journal**: Write daily entries and receive AI-powered insights
4. **Goal Tracking**: Set goals, track progress, and celebrate achievements
5. **Settings**: Customize your experience and manage your profile

## API Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /chat/history` - Retrieve chat history
- `POST /chat/message` - Send message to AI
- `GET /journal/entries` - Get journal entries
- `POST /journal/entry` - Create new journal entry
- `GET /goals` - Retrieve user goals
- `POST /goals` - Create new goal

## Development

### Running Tests
```bash
cd backend
python -m pytest
```

### Database Setup
The application automatically creates database tables on startup. For manual setup:
```bash
python database_setup.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## About

### Developer
**Metehan Haydar Erbaş** - 21 years old university student
- **Education**: International Trade and Business Administration, Open Education Computer Programming
- **Role**: AI Developer and Founder

### Company
**HAN AI** - CEO: Metehan Haydar Erbaş
- Independent AI development company focused on creating innovative life coaching solutions
- Committed to developing ethical AI applications for personal growth and development

## Disclaimer

LifeCoach AI is designed for personal development and motivation. It is not a substitute for professional therapy, counseling, or medical advice. Always consult with qualified professionals for serious personal or health concerns.

## Contact

For questions or support, please open an issue on GitHub.