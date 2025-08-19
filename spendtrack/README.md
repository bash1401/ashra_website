# SpendTrack Website

The official website for SpendTrack - Smart Expense Tracking App.

## Overview

SpendTrack is an intelligent expense tracking app that automatically detects and categorizes your expenses from SMS messages. This website serves as the landing page and provides comprehensive information about the app's features and capabilities.

## Features

### Website Features
- **Modern Design**: Clean, responsive design with smooth animations
- **SEO Optimized**: Comprehensive meta tags, structured data, and sitemap
- **Mobile Responsive**: Optimized for all device sizes
- **Fast Loading**: Optimized assets and minimal dependencies
- **Accessibility**: WCAG compliant design elements

### App Features Highlighted
- **Automatic SMS Detection**: No manual entry required
- **Real-time Spending Alerts**: Instant notifications for transactions
- **Detailed Analytics**: Comprehensive spending reports and trends
- **Privacy First**: All data stays on your device
- **Offline Functionality**: Works without internet connection
- **Multiple Bank Support**: Supports major Indian banks

## File Structure

```
spendtrack/
├── index.html          # Main landing page
├── about.html          # About page
├── privacy.html        # Privacy policy
├── terms.html          # Terms of service
├── styles.css          # Custom styles (embedded in index.html)
├── script.js           # JavaScript functionality (embedded in index.html)
├── favicon.ico         # Website favicon
├── sitemap.xml         # SEO sitemap
├── robots.txt          # Search engine directives
├── README.md           # This file
└── api/
    └── banks.json      # Bank configuration API
```

## Technical Details

### Technologies Used
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations
- **JavaScript**: Interactive functionality
- **Font Awesome**: Icons
- **Structured Data**: JSON-LD for SEO

### SEO Features
- Meta tags for social media sharing
- Open Graph and Twitter Card support
- Structured data for search engines
- Canonical URLs
- XML sitemap
- Robots.txt file

### Performance Optimizations
- Inline CSS and JavaScript to reduce HTTP requests
- Optimized images and assets
- Minimal external dependencies
- Fast loading times

## API Endpoints

### `/api/banks.json`
Provides bank configuration data for SMS parsing:
- Bank names and display names
- Sender IDs for SMS filtering
- Credit and debit patterns for transaction detection
- Ignore patterns for filtering out non-transaction SMS

## Setup and Deployment

1. **Local Development**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd spendtrack
   
   # Open index.html in a web browser
   open index.html
   ```

2. **Production Deployment**:
   - Upload all files to your web server
   - Ensure proper MIME types are set
   - Configure HTTPS for security
   - Set up proper caching headers

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Contributing

This website is part of the BashTech developer portfolio. For questions or suggestions, please contact:
- Email: subash.rathinam1401@gmail.com
- Website: https://www.bashtech.info

## License

© 2024 BashTech. All rights reserved.

## Links

- **App Download**: [Google Play Store](https://play.google.com/store/apps/details?id=com.bashtech.spendtrack)
- **Developer Website**: [BashTech](https://www.bashtech.info)
- **Privacy Policy**: [privacy.html](privacy.html)
- **Terms of Service**: [terms.html](terms.html)
