# BashTech Developer Website

A centralized developer website showcasing all BashTech mobile applications with JSON-based app management system. Features innovative apps for productivity, privacy, and everyday utility.

## 🚀 Live Website

**Main Site**: `https://yourusername.github.io/ashra_website/`

**App Pages**:
- **SafeSurf**: `https://bash1401.github.io/SafeSurf-DNS-VPN/` (Live - External)
- **SpendTrack**: `https://yourusername.github.io/ashra_website/spendtrack/` (Planned)
- **PG Pay**: `https://yourusername.github.io/ashra_website/pgpay/` (Planned)

## 📁 Project Structure

```
ashra_website/
├── index.html                    # Main developer landing page (loads from apps.json)
├── apps.json                     # JSON file managing all app information
├── spendtrack/                   # SpendTrack app section (future)
├── pgpay/                        # PG Pay app section (future)
├── sitemap.xml                   # SEO sitemap
├── robots.txt                    # Search engine configuration
├── CNAME                         # Custom domain (optional)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🎯 Key Features

### JSON-Based App Management
- **`apps.json`** - Single file to manage all app information
- **Dynamic loading** - Apps are loaded from JSON on the main page
- **Easy updates** - Just edit the JSON file to add/update apps
- **Status management** - Live vs Coming Soon status for each app

### Main Developer Page
- **Dynamic app cards** - Generated from `apps.json`
- **Status indicators** - Shows Live/Coming Soon for each app
- **Professional branding** - Consistent BashTech identity
- **Responsive design** - Works on all devices

### Individual App Pages
- **Dedicated sections** for each app
- **Consistent navigation** between apps
- **App-specific content** and features
- **Download links** to Google Play Store

## 📱 Apps Showcased

### SafeSurf 🛡️
- **Category**: DNS Privacy Protection
- **Status**: Live
- **Features**: DNS-over-HTTPS, No logs, Lightweight
- **Play Store**: `https://play.google.com/store/apps/details?id=com.bashtech.safesurfvpn`
- **Website**: `https://bash1401.github.io/SafeSurf-DNS-VPN/`

### SpendTrack 💰
- **Category**: Expense Tracking
- **Status**: Planned
- **Features**: SMS detection, Alerts, Reports
- **Play Store**: `https://play.google.com/store/apps/details?id=com.bashtech.spendtrack`

### PG Pay 🏠
- **Category**: Rent Management
- **Status**: Planned
- **Features**: Payment reminders, Receipts, History
- **Play Store**: `https://play.google.com/store/apps/details?id=com.bashtech.pgpay`

## 🛠️ Setup Instructions

### 1. Create GitHub Repository
```bash
# Create new repository named "ashra_website"
# Make it Public for free GitHub Pages
```

### 2. Upload Files
- Upload all files from the `ashra_website/` folder
- Commit with message: "Initial developer website setup"

### 3. Enable GitHub Pages
- Go to Settings → Pages
- Source: Deploy from a branch
- Branch: main, folder: /(root)
- Save

### 4. Update URLs
Replace `yourusername` with your actual GitHub username in:
- `sitemap.xml`
- Any other files with domain references

## 📝 Adding New Apps

### 1. Update apps.json
Add a new app entry to the `apps` array:

```json
{
  "name": "New App",
  "folder": "newapp",
  "icon": "🎯",
  "category": "App Category",
  "description": "App description here...",
  "status": "coming-soon",
  "playStoreUrl": "https://play.google.com/store/apps/details?id=com.bashtech.newapp",
  "features": [
    "Feature 1",
    "Feature 2",
    "Feature 3"
  ]
}
```

### 2. Create App Folder
```bash
mkdir newapp/
```

### 3. Create App Files
- `newapp/index.html` - Main app page
- `newapp/about.html` - About page
- `newapp/privacy.html` - Privacy policy

### 4. Update Configuration
- Add app to `sitemap.xml`
- Update `robots.txt` if needed

### 5. Change Status to Live
When the app is ready, change `"status": "coming-soon"` to `"status": "live"` in `apps.json`.

## 🎨 Customization

### Colors
- Primary: `#1a73e8` (Blue)
- Secondary: `#34a853` (Green)
- Background: Gradient from `#667eea` to `#764ba2`

### Branding
- Developer: BashTech
- Email: subash.rathinam1401@gmail.com
- Location: India
- Focus: Privacy & Security Apps

## 🔧 Technical Details

### Technologies Used
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with gradients and animations
- **JavaScript** - Dynamic app loading from JSON
- **Responsive Design** - Mobile-first approach
- **SEO Optimized** - Meta tags, sitemap, robots.txt

### JSON Structure
```json
{
  "developer": {
    "name": "BashTech",
    "email": "subash.rathinam1401@gmail.com",
    "playStoreUrl": "https://play.google.com/store/apps/developer?id=bashtech",
    "focus": "Privacy & Security Apps",
    "location": "India"
  },
  "apps": [
    {
      "name": "App Name",
      "folder": "appfolder",
      "icon": "🎯",
      "category": "App Category",
      "description": "App description",
      "status": "live|coming-soon",
      "playStoreUrl": "Play Store URL",
      "features": ["Feature 1", "Feature 2"]
    }
  ]
}
```

## 📊 SEO Features

- ✅ **Sitemap.xml** - All pages indexed
- ✅ **Robots.txt** - Search engine guidance
- ✅ **Meta descriptions** - Page descriptions
- ✅ **Structured navigation** - Clear site hierarchy
- ✅ **Mobile responsive** - Mobile-friendly design
- ✅ **Fast loading** - Optimized static files

## 🚀 Deployment

### GitHub Pages
- Automatic deployment from main branch
- Custom domain support via CNAME
- HTTPS enabled by default

### Custom Domain (Optional)
1. Update `CNAME` file with your domain
2. Configure DNS settings
3. Add domain in GitHub Pages settings

## 📞 Support

For questions or issues:
- **Email**: subash.rathinam1401@gmail.com
- **GitHub**: Create an issue in this repository

## 📄 License

© 2024 BashTech. All rights reserved.

---

**Your professional developer website with JSON-based app management is ready! 🎉**
