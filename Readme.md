# WSSD-JJM-CHATBOT

A comprehensive multilingual chatbot system for the Water Supply and Sanitation Department (WSSD) Jal Jeevan Mission (JJM) Public Grievance Redressal System. This system provides real-time grievance status checking, rating collection, and multilingual support (English and Marathi).

## 🚀 Features

### Core Functionality
- **Multilingual Support**: Full support for English and Marathi languages with seamless switching
- **Grievance Status Checking**: Real-time status checking using Grievance ID or registered mobile number
- **Rating System**: 5-star rating system with feedback collection linked to specific grievances
- **Knowledge Base**: Comprehensive information about WSSD, JJM, and related departments
- **Responsive UI**: Modern, mobile-friendly chat interface

### Advanced Features
- **Smart Input Validation**: Client-side and server-side validation for grievance IDs and mobile numbers
- **Anonymous Rating Prevention**: Ratings are only saved when linked to a verified grievance
- **CSV Export**: Detailed rating data export with separate columns for grievance ID and phone number
- **Session Management**: Persistent session handling for rating attribution
- **Debounced Input**: Prevents duplicate prompts and error messages

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with connection pooling
- **Data Export**: CSV generation with UTF-8 BOM for Excel compatibility
- **Validation**: Pydantic models for request validation
- **Logging**: Comprehensive logging for debugging and monitoring

### Frontend (Vanilla JavaScript)
- **UI Framework**: Pure HTML/CSS/JavaScript (no dependencies)
- **Responsive Design**: Mobile-first approach with modern CSS
- **Real-time Updates**: Dynamic chat interface with typing indicators
- **State Management**: Client-side session and conversation state handling

## 📁 Project Structure

```
WSSD-JJM-CHATBOT/
├── fastapp.py              # Main FastAPI backend application
├── index.php               # Frontend chat interface
├── database.py             # Database connection and management
├── ratings_data/           # CSV export directory
│   ├── ratings_log_YYYYMMDD.csv
│   └── ratings_log_YYYYMMDD_v2.csv
├── logo/                   # UI assets
│   ├── main_logo.png
│   ├── jjm_new_logo.svg
│   └── home.png
└── README.md               # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Modern web browser

### Backend Setup
1. **Install Dependencies**
   ```bash
   pip install fastapi uvicorn psycopg2-binary python-multipart
   ```

2. **Database Configuration**
   - Update database credentials in `database.py`
   - Ensure PostgreSQL is running and accessible

3. **Start the Server**
   ```bash
   uvicorn fastapp:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. **Deploy Files**
   - Upload `index.php` to your web server
   - Ensure `logo/` directory is accessible
   - Update API_BASE_URL in the JavaScript if needed

2. **Configuration**
   - Modify `API_BASE_URL` constant in `index.php` to point to your backend
   - Ensure CORS is properly configured if serving from different domains

## 🔧 Configuration

### Backend Configuration
- **Database Settings**: Update connection parameters in `database.py`
- **API Endpoints**: All endpoints are defined in `fastapp.py`
- **CORS Settings**: Configure allowed origins for cross-origin requests

### Frontend Configuration
- **Language Support**: Add new languages in `PGRS_SCRIPTS` object
- **API Base URL**: Update `API_BASE_URL` constant
- **UI Customization**: Modify CSS variables and styles

## 📊 API Endpoints

### Core Endpoints
- `POST /chat/` - Process user messages and return responses
- `POST /grievance/status/` - Check grievance status by ID or phone number
- `POST /rating/` - Submit rating with grievance attribution
- `GET /ratings/export` - Export all ratings as CSV

### Utility Endpoints
- `GET /health` - Health check endpoint
- `GET /ratings/stats` - Get rating statistics
- `POST /session/reset` - Reset user session

## 💾 Database Schema

### Grievance Status Table
```sql
-- Example grievance data structure
grievance_unique_number (VARCHAR)
grievance_status (VARCHAR)
grievance_logged_date (DATE)
category (VARCHAR)
district (VARCHAR)
block (VARCHAR)
taluka (VARCHAR)
gram_panchayat (VARCHAR)
subject (TEXT)
description (TEXT)
```

### Rating Data Structure
```csv
timestamp,session_id,rating,Feedback,language,grievance_id,phone_number
2024-01-15 10:30:00,session_abc123,4,Very Good,en,G-12safeg7678,N/A
2024-01-15 10:35:00,session_def456,5,Excellent,mr,N/A,9876543210
```

## 🌐 Multilingual Support

### Supported Languages
- **English (en)**: Default language with full functionality
- **Marathi (mr)**: Complete translation including error messages

### Adding New Languages
1. Add language code to `PGRS_SCRIPTS` object
2. Update language dropdown in frontend
3. Add translations for all UI elements and messages
4. Update backend error messages

### Language-Specific Features
- Dynamic UI language switching
- Grievance status messages in user's language
- Rating labels and feedback in local language
- Error messages with proper translations

## 🔒 Security Features

### Input Validation
- **Client-side**: Format validation for grievance IDs and mobile numbers
- **Server-side**: Comprehensive validation with proper error responses
- **SQL Injection Prevention**: Parameterized queries and input sanitization

### Rating Security
- **Anonymous Prevention**: Ratings only saved when linked to verified grievances
- **Session Validation**: 30-minute validity window for rating attribution
- **Data Integrity**: Proper error handling and fallback mechanisms

## 📈 Rating System

### Rating Collection
- **5-Star Scale**: 1 (Poor) to 5 (Excellent)
- **Visual Feedback**: Interactive star rating with hover effects
- **Language Support**: Rating labels in both English and Marathi
- **Grievance Linking**: Automatic attribution to checked grievances

### Rating Storage
- **CSV Export**: Daily CSV files with comprehensive data
- **Header Management**: Automatic header updates for new columns
- **Phone Number Formatting**: Proper handling to prevent Excel formatting issues
- **Data Validation**: Ensures data integrity and completeness

## 🎨 UI/UX Features

### Chat Interface
- **Modern Design**: Clean, professional interface with gradient backgrounds
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Typing Indicators**: Visual feedback during processing
- **Message History**: Persistent chat history within session

### Interactive Elements
- **Quick Actions**: Restart and clear chat buttons
- **Language Switcher**: Easy language switching with immediate UI updates
- **Suggestion Buttons**: Pre-defined quick actions for common queries
- **Rating Interface**: Intuitive 5-star rating system

## 🚨 Error Handling

### Client-Side Errors
- **Input Validation**: Immediate feedback for invalid formats
- **Network Errors**: Graceful handling of connection issues
- **Duplicate Prevention**: Debounced input to prevent spam

### Server-Side Errors
- **Database Errors**: Proper error messages and fallback handling
- **Validation Errors**: Clear, actionable error messages
- **Rate Limiting**: Protection against abuse

## 📊 Monitoring & Logging

### Logging Levels
- **INFO**: Normal operations and user interactions
- **WARNING**: Non-critical issues and edge cases
- **ERROR**: Critical errors requiring attention
- **DEBUG**: Detailed debugging information

### Key Metrics
- Rating submission rates
- Grievance status check frequency
- Language usage statistics
- Error rates and types

## 🔄 Data Flow

### Grievance Status Check
1. User enters Grievance ID or mobile number
2. Client-side format validation
3. Server-side validation and database query
4. Status formatting and response
5. Session state update for rating attribution

### Rating Submission
1. User selects rating after status check
2. System checks for valid grievance attribution
3. Rating data preparation and validation
4. CSV export with proper formatting
5. Success confirmation to user

## 🧪 Testing

### Manual Testing Checklist
- [ ] Language switching works correctly
- [ ] Grievance status checking with valid/invalid IDs
- [ ] Rating submission with and without grievance attribution
- [ ] CSV export functionality
- [ ] Mobile responsiveness
- [ ] Error handling scenarios

### Test Scenarios
1. **Valid Grievance ID**: `G-12safeg7678`
2. **Valid Mobile Number**: `9876543210`
3. **Invalid Input**: `abc123`, `12345`
4. **Anonymous Rating**: Rating without status check
5. **Language Switching**: Mid-conversation language change

## 🚀 Deployment

### Production Considerations
- **Environment Variables**: Use environment variables for sensitive data
- **HTTPS**: Enable SSL/TLS for secure communication
- **Database Connection Pooling**: Configure appropriate pool sizes
- **Log Rotation**: Implement proper log file management
- **Backup Strategy**: Regular database and CSV backups

### Performance Optimization
- **Database Indexing**: Ensure proper indexes on grievance lookup fields
- **Connection Pooling**: Optimize database connection management
- **Caching**: Consider caching for frequently accessed data
- **CDN**: Use CDN for static assets in production

## 📝 Changelog

### Version 1.0.0 (Current)
- ✅ Multilingual support (English/Marathi)
- ✅ Grievance status checking
- ✅ Rating system with grievance attribution
- ✅ CSV export functionality
- ✅ Input validation and error handling
- ✅ Responsive UI design
- ✅ Session management
- ✅ Anonymous rating prevention

### Future Enhancements
- [ ] Additional language support
- [ ] Advanced analytics dashboard
- [ ] Bulk grievance status checking
- [ ] Integration with external systems
- [ ] Automated testing suite
- [ ] Performance monitoring

## 🤝 Contributing

### Development Guidelines
1. Follow existing code style and patterns
2. Add proper error handling for new features
3. Update documentation for any changes
4. Test thoroughly across different scenarios
5. Ensure mobile compatibility

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use consistent naming conventions
- **CSS**: Follow BEM methodology for class naming
- **Comments**: Add meaningful comments for complex logic

## 📞 Support

### Common Issues
1. **Database Connection**: Check credentials and network connectivity
2. **CORS Errors**: Verify API_BASE_URL configuration
3. **CSV Export Issues**: Check file permissions and disk space
4. **Language Switching**: Clear browser cache if issues persist


