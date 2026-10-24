let stream = null;
let scanning = false;
let raf = 0;

async function postCheckIn(qrPayload) {
  const res = await fetch("/api/check-in", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ qr_payload: qrPayload }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Check-in failed");
  return data;
}

function showResult(ok, message) {
  const el = document.getElementById("result");
  el.className = "checkin-result " + (ok ? "ok" : "err");
  el.textContent = message;
}

async function handlePayload(text) {
  try {
    const data = await postCheckIn(text.trim());
    const p = data.participant || {};
    const msg = data.already_checked_in
      ? `Already checked in: ${p.name}`
      : `Welcome, ${p.name}! Check-in recorded.`;
    showResult(true, msg);
  } catch (err) {
    showResult(false, err.message || "Check-in failed");
  }
}

function scanFrame() {
  if (!scanning) return;
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  if (video.readyState !== video.HAVE_ENOUGH_DATA) {
    raf = requestAnimationFrame(scanFrame);
    return;
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const code = window.jsQR(img.data, img.width, img.height);
  if (code && code.data) {
    scanning = false;
    handlePayload(code.data);
    return;
  }
  raf = requestAnimationFrame(scanFrame);
}

document.getElementById("btnStartCam").addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const video = document.getElementById("video");
    video.srcObject = stream;
    await video.play();
    scanning = true;
    scanFrame();
    showResult(true, "Camera active — point at pass QR");
  } catch {
    showResult(false, "Camera permission denied or unavailable");
  }
});

document.getElementById("btnStopCam").addEventListener("click", () => {
  scanning = false;
  cancelAnimationFrame(raf);
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
});

document.getElementById("btnManualCheckIn").addEventListener("click", () => {
  const text = document.getElementById("manualQr").value.trim();
  if (!text) return;
  handlePayload(text);
});
