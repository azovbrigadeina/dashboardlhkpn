// Google Apps Script Web App API for Streamlit Dashboard LHKPN UNJA
// Deploy this script as a Web App:
// 1. Open your LHKPN Google Spreadsheet.
// 2. Go to Extensions -> Apps Script.
// 3. Delete any default code and paste this script.
// 4. Click Save (floppy disk icon).
// 5. Click Deploy -> New deployment.
// 6. Select type: "Web app".
// 7. Configuration:
//    - Description: "LHKPN Database & Email API"
//    - Execute as: "Me (your-email@unja.ac.id)"
//    - Who has access: "Anyone"
// 8. Click Deploy, authorize permissions, and copy the Web App URL.
// 9. Put the URL in your Streamlit secrets (.streamlit/secrets.toml) as:
//    GSHEET_API_URL = "YOUR_WEB_APP_URL"
//    GSHEET_API_KEY = "LHKPN_UNJA_SECURE_TOKEN_2026"

const API_KEY = "LHKPN_UNJA_SECURE_TOKEN_2026"; // Token pengamanan API

function doGet(e) {
  return ContentService.createTextOutput("LHKPN UNJA Database & Email API is running! Use POST requests to interact.")
    .setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e) {
  try {
    var requestData = JSON.parse(e.postData.contents);
    var key = requestData.apiKey;
    if (key !== API_KEY) {
      return ContentService.createTextOutput(JSON.stringify({ success: false, error: "Unauthorized" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    var action = requestData.action;
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Pastikan sheet Users dan Settings sudah dibuat
    initSheets(ss);
    
    if (action === "load_users") {
      var users = readUsers(ss);
      return ContentService.createTextOutput(JSON.stringify({ success: true, users: users }))
        .setMimeType(ContentService.MimeType.JSON);
    } 
    else if (action === "save_users") {
      var usersData = requestData.users;
      writeUsers(ss, usersData);
      return ContentService.createTextOutput(JSON.stringify({ success: true }))
        .setMimeType(ContentService.MimeType.JSON);
    } 
    else if (action === "load_settings") {
      var settings = readSettings(ss);
      return ContentService.createTextOutput(JSON.stringify({ success: true, settings: settings }))
        .setMimeType(ContentService.MimeType.JSON);
    } 
    else if (action === "save_settings") {
      var settingsData = requestData.settings;
      writeSettings(ss, settingsData);
      return ContentService.createTextOutput(JSON.stringify({ success: true }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    else if (action === "send_email") {
      var to = requestData.to;
      var subject = requestData.subject;
      var body = requestData.body;
      
      if (!to || !subject || !body) {
        return ContentService.createTextOutput(JSON.stringify({ success: false, error: "Missing email parameters (to, subject, body)" }))
          .setMimeType(ContentService.MimeType.JSON);
      }
      
      MailApp.sendEmail({
        to: to,
        subject: subject,
        htmlBody: body.replace(/\n/g, "<br>")
      });
      
      return ContentService.createTextOutput(JSON.stringify({ success: true }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({ success: false, error: "Unknown action: " + action }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ success: false, error: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Inisialisasi sheet jika belum ada
function initSheets(ss) {
  var userSheet = ss.getSheetByName("Users");
  if (!userSheet) {
    userSheet = ss.insertSheet("Users");
    userSheet.appendRow(["username", "password", "role", "unit"]);
    // Tambah user bawaan (default)
    userSheet.appendRow(["admin", "123456", "admin", ""]);
    userSheet.appendRow(["operator", "unja2025", "admin", ""]);
    userSheet.appendRow(["pimpinan", "lhkpn@unja", "pimpinan", ""]);
  }
  
  var settingsSheet = ss.getSheetByName("Settings");
  if (!settingsSheet) {
    settingsSheet = ss.insertSheet("Settings");
    settingsSheet.appendRow(["key", "value"]);
    // Tambah pengaturan default
    settingsSheet.appendRow(["email_subject", "PENGINGAT: Pengisian LHKPN Universitas Jambi"]);
    settingsSheet.appendRow(["email_body", "Yth. Bapak/Buku {NAMA},\n\nBerdasarkan data pemantauan e-LHKPN KPK, status LHKPN Anda saat ini: {STATUS_LHKPN}.\n\nMohon segera melakukan pengisian atau pembaharuan laporan LHKPN Anda untuk periode {BULAN}.\n\nTerima kasih atas kepatuhan Anda.\n\nSalam,\nAdmin LHKPN Universitas Jambi"]);
  }
}

// Membaca daftar pengguna dari Sheet "Users"
function readUsers(ss) {
  var sheet = ss.getSheetByName("Users");
  var values = sheet.getDataRange().getValues();
  var users = {};
  for (var i = 1; i < values.length; i++) {
    var username = values[i][0];
    if (username) {
      users[username] = {
        password: String(values[i][1]),
        role: values[i][2] || "user",
        unit: values[i][3] || null
      };
    }
  }
  return users;
}

// Menulis kembali daftar pengguna ke Sheet "Users"
function writeUsers(ss, users) {
  var sheet = ss.getSheetByName("Users");
  sheet.clear();
  sheet.appendRow(["username", "password", "role", "unit"]);
  for (var username in users) {
    sheet.appendRow([
      username,
      users[username].password,
      users[username].role,
      users[username].unit || ""
    ]);
  }
}

// Membaca pengaturan dari Sheet "Settings"
function readSettings(ss) {
  var sheet = ss.getSheetByName("Settings");
  var values = sheet.getDataRange().getValues();
  var settings = {};
  for (var i = 1; i < values.length; i++) {
    var key = values[i][0];
    if (key) {
      settings[key] = values[i][1];
    }
  }
  return settings;
}

// Menulis pengaturan ke Sheet "Settings"
function writeSettings(ss, settings) {
  var sheet = ss.getSheetByName("Settings");
  sheet.clear();
  sheet.appendRow(["key", "value"]);
  for (var key in settings) {
    sheet.appendRow([key, settings[key]]);
  }
}
