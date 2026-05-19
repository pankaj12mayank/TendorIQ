"""Email Templates"""

from .schemas import EmailTemplate, EmailType


TEMPLATES: dict[EmailType, EmailTemplate] = {
    EmailType.UPLOAD_RECEIVED: EmailTemplate(
        template_id='upload_received',
        name='File Upload Received',
        subject='File Received - TenderIQ',
        html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Received</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }
        .footer { background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .highlight { background: #e8f4fd; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">File Received</h1>
        <p>TenderIQ</p>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>Your file has been successfully uploaded and is being processed.</p>
        <div class="highlight">
            <strong>File:</strong> {{file_name}}<br>
            <strong>Tender:</strong> {{tender_name}}
        </div>
        <p>We'll notify you when processing is complete.</p>
        <a href="https://tenderiq.com/dashboard" class="button">View Dashboard</a>
    </div>
    <div class="footer">
        <p>Sent at {{timestamp}} &bull; TenderIQ - Tender Management Platform</p>
        <p>&copy; 2026 TenderIQ. All rights reserved.</p>
    </div>
</body>
</html>
        ''',
        text_content='Your file ({{file_name}}) for tender {{tender_name}} has been received and is being processed. View your dashboard for updates.',
        email_type=EmailType.UPLOAD_RECEIVED
    ),
    
    EmailType.PROCESSING_COMPLETED: EmailTemplate(
        template_id='processing_completed',
        name='Processing Completed',
        subject='Processing Complete - TenderIQ',
        html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processing Complete</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }
        .footer { background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #11998e; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .success { background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">Processing Complete</h1>
        <p>TenderIQ</p>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>Great news! Your file has been processed successfully.</p>
        <div class="success">
            <strong>File:</strong> {{file_name}}<br>
            <strong>Tender:</strong> {{tender_name}}
        </div>
        <p>You can now view the analysis results in your dashboard.</p>
        <a href="https://tenderiq.com/dashboard" class="button">View Results</a>
    </div>
    <div class="footer">
        <p>Sent at {{timestamp}} &bull; TenderIQ - Tender Management Platform</p>
    </div>
</body>
</html>
        ''',
        text_content='Your file ({{file_name}}) for tender {{tender_name}} has been processed. View your dashboard for results.',
        email_type=EmailType.PROCESSING_COMPLETED
    ),
    
    EmailType.PROCESSING_FAILED: EmailTemplate(
        template_id='processing_failed',
        name='Processing Failed',
        subject='Processing Failed - TenderIQ',
        html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processing Failed</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }
        .footer { background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #eb3349; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .error { background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">Processing Failed</h1>
        <p>TenderIQ</p>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>We encountered an issue processing your file.</p>
        <div class="error">
            <strong>File:</strong> {{file_name}}<br>
            <strong>Error:</strong> {{error}}
        </div>
        <p>Please try uploading the file again or contact support if the issue persists.</p>
        <a href="https://tenderiq.com/support" class="button">Contact Support</a>
    </div>
    <div class="footer">
        <p>Support: {{support_email}} &bull; Sent at {{timestamp}}</p>
    </div>
</body>
</html>
        ''',
        text_content='Processing failed for {{file_name}}. Error: {{error}}. Contact support at {{support_email}} for assistance.',
        email_type=EmailType.PROCESSING_FAILED
    ),
    
    EmailType.QUOTA_EXCEEDED: EmailTemplate(
        template_id='quota_exceeded',
        name='Quota Exceeded',
        subject='Quota Alert - TenderIQ',
        html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quota Alert</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }
        .footer { background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #f5576c; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .alert { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">Quota Alert</h1>
        <p>TenderIQ</p>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p>You've reached your {{feature}} limit.</p>
        <div class="alert">
            <strong>Used:</strong> {{used}}<br>
            <strong>Limit:</strong> {{limit}}
        </div>
        <p>Upgrade your plan to continue using this feature without interruption.</p>
        <a href="{{upgrade_url}}" class="button">Upgrade Now</a>
    </div>
    <div class="footer">
        <p>Sent at {{timestamp}} &bull; TenderIQ - Tender Management Platform</p>
    </div>
</body>
</html>
        ''',
        text_content='Quota alert: You\'ve used {{used}} out of {{limit}} {{feature}}. Upgrade at {{upgrade_url}} to continue.',
        email_type=EmailType.QUOTA_EXCEEDED
    ),
    
    EmailType.SUBSCRIPTION_ALERT: EmailTemplate(
        template_id='subscription_alert',
        name='Subscription Alert',
        subject='Subscription Alert - TenderIQ',
        html_content='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Alert</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }
        .footer { background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #4facfe; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">Subscription Alert</h1>
        <p>TenderIQ</p>
    </div>
    <div class="content">
        <p>Hello,</p>
        <p><strong>Alert Type:</strong> {{alert_type}}</p>
        <p>{{message}}</p>
        <a href="{{billing_url}}" class="button">Manage Subscription</a>
    </div>
    <div class="footer">
        <p>Sent at {{timestamp}} &bull; TenderIQ - Tender Management Platform</p>
    </div>
</body>
</html>
        ''',
        text_content='Subscription alert ({{alert_type}}): {{message}}. Manage at {{billing_url}}.',
        email_type=EmailType.SUBSCRIPTION_ALERT
    ),
}


def get_template(email_type: EmailType) -> EmailTemplate:
    return TEMPLATES.get(email_type, TEMPLATES[EmailType.GENERIC])


def get_all_templates() -> list[EmailTemplate]:
    return list(TEMPLATES.values())