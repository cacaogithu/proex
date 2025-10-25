import express from 'express';
import bodyParser from 'body-parser';
import { processAndSendResults } from './email-service.js';

const app = express();
app.use(bodyParser.json());

app.post('/send-results', async (req, res) => {
  try {
    const { submissionId, recipientEmail, docxFiles } = req.body;

    if (!submissionId || !recipientEmail || !docxFiles || docxFiles.length === 0) {
      return res.status(400).json({
        error: 'Missing required fields: submissionId, recipientEmail, docxFiles'
      });
    }

    console.log(`\n📨 Received request to send results for ${submissionId}`);
    
    const result = await processAndSendResults(submissionId, recipientEmail, docxFiles);

    res.json({
      success: true,
      message: 'Results uploaded to Google Drive and email sent successfully',
      ...result
    });
  } catch (error) {
    console.error('Error processing request:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'email-service' });
});

const PORT = process.env.EMAIL_SERVICE_PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`📧 Email service listening on port ${PORT}`);
});
