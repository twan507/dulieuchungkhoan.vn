# Đăng ký Task Scheduler cho lát cắt ingester + OMO (spec 2026-08-26 §3.8/§4.5).
# Chạy: pwsh scripts/register-tasks.ps1     (idempotent — ghi đè task cùng tên)
#
# LƯU Ý: task `dlck-ingester` được tạo ở trạng thái DISABLED. Chỉ bật sau khi
# phiên đo trong giờ giao dịch xong và chủ dự án duyệt luật SM/dedup (spec §3.5):
#     Enable-ScheduledTask -TaskName dlck-ingester
#
# ⚠️ Dùng cmdlet ScheduledTasks, KHÔNG dùng schtasks.exe: bản schtasks trước đây
# đăng ký nhầm lệnh rỗng (`python -m `) vì tham số hàm đặt tên `$args` — trùng
# BIẾN TỰ ĐỘNG của PowerShell nên thân hàm đọc ra rỗng. Task vẫn "Ready", vẫn
# chạy đúng giờ, và chết câm mỗi lần. Kiểm nghiệm thu phải soi LỆNH, không soi
# trạng thái — xem hàm Assert-TaskCommand ở cuối file.

$repo    = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$logDir  = Join-Path (Split-Path $repo -Parent) "dlck-runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$uv = (Get-Command uv -ErrorAction Stop).Source

function Register-DlckTask {
    param(
        [Parameter(Mandatory)][string] $TaskName,
        [Parameter(Mandatory)][string] $AtTime,      # "HH:mm"
        [Parameter(Mandatory)][string] $ModuleArgs,  # ví dụ "etl omo"
        [Parameter(Mandatory)][string] $LogFile
    )
    $inner = 'cd /d "{0}" && set PYTHONIOENCODING=utf-8 && "{1}" run python -m {2} >> "{3}" 2>&1' `
             -f $backend, $uv, $ModuleArgs, (Join-Path $logDir $LogFile)
    $action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $inner"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $AtTime
    # StartWhenAvailable: máy ngủ/tắt qua giờ chạy thì chạy bù khi bật lại.
    # RestartCount/RestartInterval: tự khởi động lại khi tiến trình chết (spec §3.8).
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) `
                    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 12)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Force | Out-Null
    Write-Host ("  + {0,-16} {1}  ->  python -m {2}" -f $TaskName, $AtTime, $ModuleArgs)
}

function Assert-TaskCommand {
    <#  Nghiệm thu: soi LỆNH thật của task, không soi trạng thái.  #>
    param([string] $TaskName, [string] $MustContain)
    $arg = (Get-ScheduledTask -TaskName $TaskName).Actions[0].Arguments
    if ($arg -notmatch [regex]::Escape($MustContain)) {
        throw "Task $TaskName đăng ký SAI lệnh — thiếu '$MustContain'. Lệnh thật: $arg"
    }
}

Write-Host "Đăng ký job crawl OMO (4 mốc/ngày làm việc):"
foreach ($t in @("11:30", "15:30", "18:00", "21:30")) {
    $name = "dlck-omo-" + ($t -replace ':', '')
    Register-DlckTask -TaskName $name -AtTime $t -ModuleArgs "etl omo" -LogFile "omo.log"
    Assert-TaskCommand -TaskName $name -MustContain "python -m etl omo"
}

Write-Host "Đăng ký ingester theo phiên (08:30, tự thoát sau đối chứng ~15:05):"
Register-DlckTask -TaskName "dlck-ingester" -AtTime "08:30" -ModuleArgs "ingester" -LogFile "ingester-task.log"
Assert-TaskCommand -TaskName "dlck-ingester" -MustContain "python -m ingester "
Disable-ScheduledTask -TaskName "dlck-ingester" | Out-Null
Write-Host "  ! dlck-ingester đang DISABLED — bật sau gate phiên đo (spec §3.5)"

Write-Host "`nĐã kiểm lệnh của cả 5 task. Xem lại bất cứ lúc nào:"
Write-Host '  Get-ScheduledTask -TaskName "dlck-*" | % { $_.TaskName + " -> " + $_.Actions[0].Arguments }'
Write-Host "`n⚠️ Task chạy với tài khoản đang đăng nhập (Interactive). Muốn chạy cả khi"
Write-Host "   không đăng nhập, đăng ký lại bằng quyền admin với -LogonType S4U."
