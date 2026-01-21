import os
from agents.deals import Opportunity
from agents.agent import Agent
from litellm import completion
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class MessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE
    MODEL = "gemini/gemini-2.5-flash-lite"  # LiteLLM format: gemini/ prefix for Gemini API

    def __init__(self):
        """
        Set up this object to either do push notifications via email with smtplib,
        whichever is specified in the constants
        """
        self.log("Messaging Agent is initializing")
        self.gmail_pwd = os.getenv("GMAIL_PWD")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_to = os.getenv("GMAIL_TO")
        self.log("Messaging Agent has been initialized")

    def _create_email_html_content(self, text):
        """
        Create HTML formatted email content for deal alerts
        
        Args:
            text: The message text to include in the email
            
        Returns:
            str: HTML formatted email content
        """
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .container {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }}
                    .content {{
                        background: white;
                        border-radius: 8px;
                        padding: 25px;
                        margin-top: 20px;
                    }}
                    h2 {{
                        color: #ffffff;
                        margin: 0;
                        font-size: 24px;
                    }}
                    .alert-icon {{
                        font-size: 48px;
                        text-align: center;
                        margin-bottom: 10px;
                    }}
                    .message {{
                        font-size: 16px;
                        color: #444;
                        line-height: 1.8;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #ffffff;
                    }}
                    a {{
                        color: #667eea;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert-icon">🎯</div>
                    <h2>Amazing Deal Detected!</h2>
                    <div class="content">
                        <p class="message">{text}</p>
                    </div>
                    <div class="footer">
                        <p>🤖 Sent by your Price Predictor Agent</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html_content
    
    def push(self, text):
        """
        Send a message via email using smtplib with MIME formatting
        """
        self.log("Messaging Agent is sending a push notification")
        
        try:
            # Create multipart message with both HTML and plain text
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '🔔 Deal Alert - Don\'t Miss This Opportunity!'
            msg['From'] = self.gmail_user
            msg['To'] = self.gmail_to
            
            # Plain text version
            text_part = MIMEText(text, 'plain', 'utf-8')
            
            # HTML version with nice formatting
            html_content = self._create_email_html_content(text)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # Attach parts (plain text first, then HTML as preferred)
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect to Gmail SMTP server with TLS encryption
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()  # Identify ourselves to the SMTP server
                server.starttls()  # Secure the connection
                server.ehlo()  # Re-identify as an encrypted connection
                server.login(self.gmail_user, self.gmail_pwd)
                server.send_message(msg)
            
            self.log("✅ Email sent successfully!")
            
        except Exception as e:
            self.log(f"❌ Failed to send email: {str(e)}")
            raise
       

    def alert(self, opportunity: Opportunity):
        """
        Make an alert about the specified Opportunity
        """
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10] + "... "
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(
        self, description: str, deal_price: float, estimated_true_value: float
    ) -> str:
        user_prompt = "Please summarize this great deal in 2-3 sentences to be sent as an exciting push notification alerting the user about this deal.\n"
        user_prompt += f"Item Description: {description}\nOffered Price: {deal_price}\nEstimated true value: {estimated_true_value}"
        user_prompt += "\n\nRespond only with the 2-3 sentence message which will be used to alert & excite the user about this deal"
        response = completion(
            model=self.MODEL,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        return response.choices[0].message.content

    def notify(self, description: str, deal_price: float, estimated_true_value: float, url: str):
        """
        Make an alert about the specified details
        """
        self.log("Messaging Agent is using Claude to craft the message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text+ "... " + url)
        self.log("Messaging Agent has completed")
