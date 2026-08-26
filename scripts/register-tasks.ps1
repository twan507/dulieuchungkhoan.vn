# Đăng ký Task Scheduler cho lát cắt ingester + OMO (spec 2026-08-26 §3.8/§4.5).
# Chạy: pwsh scripts/register-tasks.ps1     (idempotent — /F ghi đè task cùng tên)
#
# LƯU Ý: task `dlck-ingester` được tạo ở trạng thái DISABLED. Chỉ bật sau khi
# phiên đo trong giờ giao dịch xong và chủ dự án duyệt luật SM/dedup (spec §3.5):
#     schtasks /Change /TN dlck-ingester /ENABLE

$repo    = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$logDir  = Join-Path (Split-Path $repo -Parent) "dlck-runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$uv = (Get-Command uv).Source

function Register-DlckTask($name, $time, $args, $logFile) {
    $cmd = "cd /d `"$backend`" && set PYTHONIOENCODING=utf-8 && `"$uv`" run python -m $args"
    schtasks /Create /F /TN $name /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST $time `
        /TR "cmd /c $cmd >> `"$logDir\$logFile`" 2>&1" | Out-Null
    Write-Host "  + $name  ($time)"
}

Write-Host "Đăng ký job crawl OMO (4 mốc/ngày làm việc):"
foreach ($t in @("11:30", "15:30", "18:00", "21:30")) {
    Register-DlckTask "dlck-omo-$($t -replace ':','')" $t "etl omo" "omo.log"
}

Write-Host "Đăng ký ingester theo phiên (08:30, tự thoát sau đối chứng ~15:05):"
Register-DlckTask "dlck-ingester" "08:30" "ingester" "ingester-task.log"
schtasks /Change /TN "dlck-ingester" /DISABLE | Out-Null
Write-Host "  ! dlck-ingester đang DISABLED — bật sau gate phiên đo (spec §3.5)"

Write-Host "`nXong. Kiểm: schtasks /Query /TN dlck-ingester"
