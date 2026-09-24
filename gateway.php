<?php
// =======================
// 🔐 TOKEN-AUTH GATEWAY (Render Hardened)
// =======================

ob_start(); // Prevent premature output (important for setcookie / header)

$logFile      = __DIR__ . "/debug_log.txt";
$tokenDB      = __DIR__ . "/tokens.json";
$payloadFile  = __DIR__ . "/payload_core.b64";
$cacheDir     = __DIR__ . "/cache_site";
$decryptedZip = __DIR__ . "/decrypted_payload.zip";

// -- Log helper
function logEntry($msg) {
    global $logFile;
    file_put_contents($logFile, "[" . date("Y-m-d H:i:s") . "] $msg\n", FILE_APPEND);
}

// -- Safe recursive delete (works on nested folders too)
function recursiveDelete($dir) {
    if (!is_dir($dir)) return;
    $items = array_diff(scandir($dir), ['.', '..']);
    foreach ($items as $item) {
        $path = "$dir/$item";
        if (is_dir($path)) {
            recursiveDelete($path);
        } else {
            @unlink($path);
        }
    }
    @rmdir($dir);
}

// =========================
// 🔑 Step 1: Validate Token
// =========================

$token = $_GET['t'] ?? $_COOKIE['stealth_access'] ?? null;
if (!$token || !file_exists($tokenDB)) {
    logEntry("❌ No token or token DB missing.");
    exit("Invalid request.");
}

$db = json_decode(file_get_contents($tokenDB), true);
if (!isset($db[$token])) {
    logEntry("❌ Invalid token: $token");
    exit("Unauthorized");
}

$record = $db[$token];
if (($record['status'] ?? '') !== 'active') {
    logEntry("❌ Token $token is revoked or inactive.");
    exit("Access denied.");
}

if (isset($record['expires']) && strtotime($record['expires']) < time()) {
    logEntry("❌ Token expired: $token");
    exit("Expired token.");
}

// =========================
// 🔄 Step 2: Reassemble .b64
// =========================

if (!file_exists($payloadFile)) {
    $chunks = glob(__DIR__ . "/payload_part_*.b64");
    natsort($chunks);
    if (!$chunks) {
        logEntry("❌ No payload chunks found (payload_part_*.b64).");
        exit("Missing chunks.");
    }

    $out = fopen($payloadFile, "wb");
    foreach ($chunks as $chunk) {
        $data = file_get_contents($chunk);
        if ($data === false) {
            fclose($out);
            logEntry("❌ Failed reading chunk: $chunk");
            exit("Read error.");
        }
        fwrite($out, $data);
        logEntry("📥 Merged chunk: " . basename($chunk));
    }
    fclose($out);
    logEntry("✅ Finalized combined payload: payload_core.b64");
} else {
    logEntry("⚠️ Skipping reassembly — payload already exists.");
}

// =========================
// 🔐 Step 3: Decrypt Payload
// =========================

$key = base64_decode($record['key']);
$iv  = base64_decode($record['iv']);

$raw = base64_decode(file_get_contents($payloadFile));
if (!$raw) {
    logEntry("❌ Base64 decode failed.");
    exit("Corrupt payload.");
}

$decrypted = openssl_decrypt($raw, "aes-256-cbc", $key, OPENSSL_RAW_DATA, $iv);
if (!$decrypted) {
    logEntry("❌ Decryption failed.");
    exit("Unable to decrypt.");
}

file_put_contents($decryptedZip, $decrypted);
logEntry("📦 Wrote decrypted archive: $decryptedZip");

// =============================
// 📦 Step 4: Extract to cache
// =============================

if (is_dir($cacheDir)) {
    logEntry("🧹 Cleaning existing cache directory...");
    recursiveDelete($cacheDir);
}
if (!mkdir($cacheDir, 0755, true) && !is_dir($cacheDir)) {
    logEntry("❌ Failed to create cache directory.");
    exit("Cache error.");
}
file_put_contents("$cacheDir/.timestamp", time());

$zip = new ZipArchive();
if ($zip->open($decryptedZip) === TRUE) {
    $zip->extractTo($cacheDir);
    $zip->close();
    logEntry("✅ Extracted to cache: $cacheDir");
} else {
    logEntry("❌ Zip extraction failed.");
    exit("Unzip error.");
}

// =============================
// 🍪 Step 5: Cookie + Redirect
// =============================

setcookie("stealth_access", $token, [
    'expires'  => time() + 6 * 3600,
    'path'     => '/',
    'secure'   => true,
    'httponly' => true,
    'samesite' => 'Strict'
]);

// RECOMMENDATION 4: Append the token to the URL to guarantee fallback auth
header("Location: navigate.php?t=" . urlencode($token));
exit;
?>
