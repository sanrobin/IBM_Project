// frontend logic for index page
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const log = document.getElementById('log');
  log.textContent = "Requesting login...";
  try {
    const res = await fetch('/api/login', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email, password})
    });
    const data = await res.json();
    log.textContent = JSON.stringify(data, null, 2);
    if(res.ok && data.otp_preview){
      // demo: show OTP to user and navigate to MFA page
      localStorage.setItem('demo_otp_preview', data.otp_preview);
      localStorage.setItem('demo_email', email);
      window.location = '/mfa';
    }
  } catch(err){
    log.textContent = "Error: " + err.message;
  }
});
