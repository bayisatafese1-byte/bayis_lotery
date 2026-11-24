<?php
// =======================================================
// Lucky200 - XAMPP MySQL Connection Test
// =======================================================

$host = "localhost";
$user = "root";
$pass = "";
$db   = "lucky200";

$conn = mysqli_connect($host, $user, $pass, $db);

if (!$conn) {
    die("<h3 style='color:red;'>XAMPP MySQL Connection failed: " . mysqli_connect_error() . "</h3>");
}

echo "<div style='font-family:sans-serif; padding:20px; border:2px solid #10b981; border-radius:12px; background:#ecfdf5; max-width:600px; margin:40px auto;'>";
echo "<h2 style='color:#065f46; margin-top:0;'>✅ XAMPP MySQL Connected Successfully!</h2>";
echo "<p><strong>Database:</strong> $db</p>";
echo "<p><strong>Host:</strong> $host (User: $user)</p>";

$res = mysqli_query($conn, "SELECT COUNT(*) as total, SUM(CASE WHEN status='available' THEN 1 ELSE 0 END) as open_cnt FROM numbers");
if ($row = mysqli_fetch_assoc($res)) {
    echo "<p><strong>Total Raffle Numbers:</strong> " . $row['total'] . "</p>";
    echo "<p><strong>Available Numbers:</strong> " . $row['open_cnt'] . "</p>";
}

echo "<hr style='border:none; border-top:1px solid #a7f3d0; margin:15px 0;'>";
echo "<p style='font-size:12px; color:#047857;'>You can also manage this database directly in phpMyAdmin at: <a href='http://localhost/phpmyadmin' target='_blank'>http://localhost/phpmyadmin</a></p>";
echo "</div>";

mysqli_close($conn);
?>
