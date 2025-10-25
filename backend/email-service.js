import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let gmailConnectionSettings = null;
let driveConnectionSettings = null;

async function getGmailAccessToken() {
  if (gmailConnectionSettings?.settings?.expires_at && 
      new Date(gmailConnectionSettings.settings.expires_at).getTime() > Date.now()) {
    return gmailConnectionSettings.settings.access_token;
  }
  
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  gmailConnectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=google-mail',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0]);

  const accessToken = gmailConnectionSettings?.settings?.access_token || 
                     gmailConnectionSettings?.settings?.oauth?.credentials?.access_token;

  if (!gmailConnectionSettings || !accessToken) {
    throw new Error('Gmail not connected');
  }
  return accessToken;
}

async function getDriveAccessToken() {
  if (driveConnectionSettings?.settings?.expires_at && 
      new Date(driveConnectionSettings.settings.expires_at).getTime() > Date.now()) {
    return driveConnectionSettings.settings.access_token;
  }
  
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  driveConnectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=google-drive',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0]);

  const accessToken = driveConnectionSettings?.settings?.access_token || 
                     driveConnectionSettings?.settings?.oauth?.credentials?.access_token;

  if (!driveConnectionSettings || !accessToken) {
    throw new Error('Google Drive not connected');
  }
  return accessToken;
}

async function getGmailClient() {
  const accessToken = await getGmailAccessToken();
  const oauth2Client = new google.auth.OAuth2();
  oauth2Client.setCredentials({ access_token: accessToken });
  return google.gmail({ version: 'v1', auth: oauth2Client });
}

async function getDriveClient() {
  const accessToken = await getDriveAccessToken();
  const oauth2Client = new google.auth.OAuth2();
  oauth2Client.setCredentials({ access_token: accessToken });
  return google.drive({ version: 'v3', auth: oauth2Client });
}

async function findOrCreateFolder(drive, folderName, parentId = null) {
  const query = parentId 
    ? `name='${folderName}' and '${parentId}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false`
    : `name='${folderName}' and mimeType='application/vnd.google-apps.folder' and trashed=false`;

  const response = await drive.files.list({
    q: query,
    fields: 'files(id, name)',
    spaces: 'drive'
  });

  if (response.data.files && response.data.files.length > 0) {
    console.log(`📁 Found existing folder: ${folderName} (${response.data.files[0].id})`);
    return response.data.files[0].id;
  }

  const folderMetadata = {
    name: folderName,
    mimeType: 'application/vnd.google-apps.folder'
  };
  
  if (parentId) {
    folderMetadata.parents = [parentId];
  }

  const folder = await drive.files.create({
    requestBody: folderMetadata,
    fields: 'id'
  });

  console.log(`📁 Created new folder: ${folderName} (${folder.data.id})`);
  return folder.data.id;
}

export async function uploadToGoogleDrive(filePath, fileName, submissionId, recipientEmail) {
  try {
    console.log(`📤 Uploading ${fileName} to Google Drive...`);
    const drive = await getDriveClient();

    const parentFolderId = await findOrCreateFolder(drive, 'ProEx - Cartas EB-2 NIW');
    const submissionFolderId = await findOrCreateFolder(drive, submissionId, parentFolderId);

    const fileMetadata = {
      name: fileName,
      parents: [submissionFolderId]
    };

    // Detect file type
    const mimeType = filePath.endsWith('.pdf') 
      ? 'application/pdf'
      : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    
    const media = {
      mimeType: mimeType,
      body: fs.createReadStream(filePath)
    };

    const file = await drive.files.create({
      requestBody: fileMetadata,
      media: media,
      fields: 'id, name, webViewLink, webContentLink'
    });

    if (recipientEmail) {
      await drive.permissions.create({
        fileId: file.data.id,
        requestBody: {
          type: 'user',
          role: 'writer',
          emailAddress: recipientEmail
        },
        sendNotificationEmail: false
      });
      console.log(`🔐 Shared with ${recipientEmail} (writer access)`);
    }

    console.log(`✅ Uploaded: ${file.data.name} (${file.data.id})`);
    return {
      fileId: file.data.id,
      fileName: file.data.name,
      webViewLink: file.data.webViewLink,
      webContentLink: file.data.webContentLink
    };
  } catch (error) {
    console.error('❌ Error uploading to Google Drive:', error);
    throw error;
  }
}

export async function sendEmailWithDriveLinks(recipientEmail, submissionId, driveFiles) {
  try {
    console.log(`📧 Sending email to ${recipientEmail}...`);
    const gmail = await getGmailClient();

    const fileLinks = driveFiles.map(f => 
      `• <a href="${f.webViewLink}">${f.fileName}</a>`
    ).join('\n    ');

    const htmlBody = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background-color: #4285f4; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
    .files-list { background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #4285f4; }
    .footer { margin-top: 30px; font-size: 12px; color: #666; text-align: center; }
    a { color: #4285f4; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎉 Suas Cartas EB-2 NIW Estão Prontas!</h1>
    </div>
    <div class="content">
      <p>Olá!</p>
      
      <p>Excelentes notícias! Suas cartas de recomendação para o visto EB-2 NIW foram processadas com sucesso e já estão disponíveis no seu Google Drive.</p>
      
      <div class="files-list">
        <h3>📄 Documentos Gerados:</h3>
        <p>${fileLinks}</p>
      </div>
      
      <p><strong>O que fazer agora:</strong></p>
      <ol>
        <li>Clique nos links acima para visualizar cada carta no Google Drive</li>
        <li>Revise o conteúdo e faça ajustes se necessário (os documentos são editáveis)</li>
        <li>Baixe os documentos finais em formato DOCX ou PDF</li>
      </ol>
      
      <p><strong>ID da Submissão:</strong> <code>${submissionId}</code></p>
      
      <p>Todos os documentos estão salvos na pasta <strong>"ProEx - Cartas EB-2 NIW"</strong> no seu Google Drive.</p>
      
      <div class="footer">
        <p>Este é um email automático do ProEx Platform.<br>
        Em caso de dúvidas, entre em contato com nossa equipe.</p>
      </div>
    </div>
  </div>
</body>
</html>
    `.trim();

    const subject = `✅ Cartas EB-2 NIW Prontas - ID: ${submissionId}`;
    
    const message = [
      `To: ${recipientEmail}`,
      `Subject: ${subject}`,
      'MIME-Version: 1.0',
      'Content-Type: text/html; charset=utf-8',
      '',
      htmlBody
    ].join('\n');

    const encodedMessage = Buffer.from(message)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    const result = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage
      }
    });

    console.log(`✅ Email sent successfully! Message ID: ${result.data.id}`);
    return {
      messageId: result.data.id,
      success: true
    };
  } catch (error) {
    console.error('❌ Error sending email:', error);
    throw error;
  }
}

export async function processAndSendResults(submissionId, recipientEmail, docxFiles) {
  try {
    console.log(`\n🚀 Processing submission ${submissionId} for ${recipientEmail}`);
    console.log(`📦 Files to upload: ${docxFiles.length}`);

    const driveFiles = [];
    for (const docxPath of docxFiles) {
      const fileName = path.basename(docxPath);
      const uploadedFile = await uploadToGoogleDrive(docxPath, fileName, submissionId, recipientEmail);
      driveFiles.push(uploadedFile);
    }

    const emailResult = await sendEmailWithDriveLinks(recipientEmail, submissionId, driveFiles);

    console.log(`\n✅ All done! ${driveFiles.length} files uploaded and email sent.`);
    return {
      success: true,
      filesUploaded: driveFiles.length,
      driveFiles: driveFiles,
      emailSent: emailResult.success
    };
  } catch (error) {
    console.error('❌ Error in processAndSendResults:', error);
    throw error;
  }
}
