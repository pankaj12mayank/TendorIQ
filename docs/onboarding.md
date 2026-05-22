# Onboarding Guide

Welcome to TenderIQ! This guide will help you get started with the platform.

---

## For Users

### 1. Getting Started

1. **Sign Up**: Visit [tenderiq.com](https://tenderiq.com) and sign up
2. **Verify Email**: Check your inbox for verification link
3. **Complete Profile**: Add your name and organization
4. **Select Plan**: Choose a plan (Starter is free)

### 2. Your First Tender

```markdown
Step 1: Create a tender
- Click "New Tender" button
- Enter title, description, deadline
- Set budget range

Step 2: Upload documents
- Drag & drop files or click to browse
- Support: PDF, DOC, DOCX, TXT
- Each file max 50MB

Step 3: AI Analysis
- Select document
- Click "Analyze"
- Choose analysis type:
  - 📊 Risk Analysis
  - 📝 Summary
  - 🔍 Data Extraction

Step 4: Export
- Select format (PDF, Excel, Word)
- Click "Export"
- Download or email
```

### 3. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + N` | New tender |
| `Ctrl + U` | Upload document |
| `Ctrl + /` | Search |
| `Escape` | Close modal |

---

## For Administrators

### 1. Organization Setup

1. **Invite Team**: Settings → Team → Invite
2. **Set Roles**: Assign roles (Admin, Manager, Analyst, Viewer)
3. **Configure Integrations**: Settings → Integrations
4. **Upload Logo**: Settings → Organization

### 2. RBAC Permissions

| Role | Permissions |
|------|-------------|
| Admin | Full access, user management, billing |
| Manager | Create/edit tenders, manage team |
| Analyst | Create tenders, run analysis |
| Viewer | Read-only access |

### 3. Billing

1. **View Plan**: Settings → Billing
2. **Upgrade**: Click "Change Plan"
3. **Add Payment**: Add credit card
4. **Invoices**: View in billing history

---

## For Developers

### 1. API Setup

```bash
# Get API key
# Go to Settings → API Keys → Create

# Test API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.tenderiq.com/api/v1/tenders
```

### 2. SDK Installation

```bash
# JavaScript
npm install @tendoriq/sdk

# Python
pip install tenderiq
```

### 3. Webhooks

Configure webhooks in Settings → Webhooks:

```javascript
// Example: Handle tender created
app.post('/webhooks/tenderiq', (req, res) => {
  const event = req.body;
  
  switch (event.type) {
    case 'tender.created':
      console.log('New tender:', event.data);
      break;
    case 'document.uploaded':
      console.log('New document:', event.data);
      break;
  }
  
  res.json({ received: true });
});
```

---

## Best Practices

### Document Management
- Use consistent naming: `[Client] - [Project] - [Date]`
- Add tags for filtering
- Regularly archive old tenders
- Use folders for organization

### AI Analysis
- Start with Summary to understand document
- Use Extraction for specific data fields
- Use Risk Analysis for compliance checking
- Review AI suggestions before finalizing

### Team Collaboration
- Use @mentions in comments
- Set up notifications for important updates
- Share exported reports with stakeholders

---

## Common Tasks

### How do I...

**...upload multiple files?**
> Use batch upload - select all files at once

**...run analysis on multiple documents?**
> Select documents in list view, click "Analyze All"

**...export only certain sections?**
> Use selective export - choose specific sections

**...give someone temporary access?**
> Create a viewer account with expiration date

**...track who made changes?**
> View audit log in tender details

---

## Getting Help

- 📖 [Documentation](https://docs.tenderiq.com)
- 💬 [Discord Community](https://discord.gg/tenderiq)
- 📧 support@tenderiq.com
- 📞 1-800-TENDERIQ

---

## Training Resources

- 🎥 Video tutorials on YouTube
- 📚 Interactive demos
- 📝 Sample tenders for practice
- 🔧 API examples on GitHub