# Đăng ký Task Scheduler cho lát cắt ingester + OMO (spec 2026-08-26 §3.8/§4.5).
# Chạy: pwsh scripts/register-tasks.ps1     (chạy lại được — ghi đè task cùng tên)
# NGOẠI LỆ: `dlck-ingester-measure` là task MỘT LẦN, đã tồn tại thì giữ nguyên,
# không nạp mốc mới — xem chốt chặn ở cuối file và lý do tại đó.
#
# GATE GHI TICK — MỞ 2026-08-26 (quyết định chủ dự án). `dlck-ingester` nay đăng ký ở
# trạng thái BẬT. Trước đó nó bị Disable ngay sau khi đăng ký để chặn ghi thật cho tới
# khi có phiên đo trong giờ giao dịch; điều kiện đó nay chuyển thành CHẠY SONG SONG:
# phiên ghi thật đi kèm một phiên `--measure` bắt frame thô làm lưới an toàn, nên bản
# thô vẫn còn nguyên nếu đường chuẩn hoá từ chối frame phiên sáng/ATO.
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
        [Parameter(Mandatory)][string] $LogFile,
        [switch] $Once            # chạy đúng MỘT lần vào ngày làm việc kế tiếp
    )
    $inner = 'cd /d "{0}" && set PYTHONIOENCODING=utf-8 && "{1}" run python -m {2} >> "{3}" 2>&1' `
             -f $backend, $uv, $ModuleArgs, (Join-Path $logDir $LogFile)
    $action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $inner"
    if ($Once) {
        $d = (Get-Date).Date.AddDays(1)
        while ($d.DayOfWeek -in 'Saturday', 'Sunday') { $d = $d.AddDays(1) }
        $hm = [datetime]::ParseExact($AtTime, 'HH:mm', [cultureinfo]::InvariantCulture)
        $trigger = New-ScheduledTaskTrigger -Once -At $d.AddHours($hm.Hour).AddMinutes($hm.Minute)
    } else {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $AtTime
    }
    # StartWhenAvailable: máy ngủ/tắt qua giờ chạy thì chạy bù khi bật lại.
    # RestartCount/RestartInterval: tự khởi động lại khi tiến trình chết (spec §3.8).
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) `
                    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 12)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Force | Out-Null
    $when = if ($Once) { "$AtTime (một lần)" } else { $AtTime }
    Write-Host ("  + {0,-24} {1,-16}  ->  python -m {2}" -f $TaskName, $when, $ModuleArgs)
}

function Assert-TaskCommand {
    <#  Nghiệm thu: soi LỆNH thật của task, không soi trạng thái.  #>
    param([string] $TaskName, [string] $MustContain, [string] $MustNotContain)
    $arg = (Get-ScheduledTask -TaskName $TaskName).Actions[0].Arguments
    if ($arg -notmatch [regex]::Escape($MustContain)) {
        throw "Task $TaskName đăng ký SAI lệnh — thiếu '$MustContain'. Lệnh thật: $arg"
    }
    if ($MustNotContain -and $arg -match [regex]::Escape($MustNotContain)) {
        throw "Task $TaskName đăng ký SAI lệnh — KHÔNG được chứa '$MustNotContain'. Lệnh thật: $arg"
    }
}

Write-Host "Đăng ký job crawl OMO (4 mốc/ngày làm việc):"
foreach ($t in @("11:30", "15:30", "18:00", "21:30")) {
    $name = "dlck-omo-" + ($t -replace ':', '')
    Register-DlckTask -TaskName $name -AtTime $t -ModuleArgs "etl omo" -LogFile "omo.log"
    Assert-TaskCommand -TaskName $name -MustContain "python -m etl omo"
}

Write-Host "Đăng ký refdata (08:00 ngày làm việc — danh bạ tươi TRƯỚC ingester 08:30 và ETL giá):"
Register-DlckTask -TaskName "dlck-refdata" -AtTime "08:00" -ModuleArgs "etl refdata" -LogFile "refdata.log"
Assert-TaskCommand -TaskName "dlck-refdata" -MustContain "python -m etl refdata"

Write-Host "Đăng ký ingester theo phiên (08:30, tự thoát sau đối chứng ~15:05):"
Register-DlckTask -TaskName "dlck-ingester" -AtTime "08:30" -ModuleArgs "ingester" -LogFile "ingester-task.log"
Assert-TaskCommand -TaskName "dlck-ingester" -MustContain "python -m ingester " -MustNotContain "--measure"
Enable-ScheduledTask -TaskName "dlck-ingester" | Out-Null
# Nghiệm thu chính thứ commit này sinh ra để đổi (§3.5: kiểm cái nó THỰC SỰ ở trạng thái
# nào, đừng tin lệnh vừa gọi đã có tác dụng).
if ((Get-ScheduledTask -TaskName "dlck-ingester").State -eq "Disabled") {
    throw "dlck-ingester vẫn DISABLED sau khi Enable — ghi tick sẽ không chạy."
}
Write-Host "  * dlck-ingester ĐANG BẬT — ghi tick thật (gate mở 2026-08-26)"

# Phiên đo song song: bắt frame THÔ ra JSONL trong khi phiên ghi chạy. Đây là điều kiện
# gate còn lại (phủ phiên sáng + ATO + tính chất SM — spec ClickHouse §4.1), và đồng thời
# là lưới an toàn cho chính phiên ghi đầu tiên. Đăng ký MỘT LẦN: cần đúng một ngày trọn,
# ~110 MB gzip; chạy hằng ngày thì tích rác đĩa vô ích.
# Script tự khai idempotent, nhưng task một-lần thì KHÔNG: chạy lại vì bất cứ lý do gì
# (thêm mốc OMO, sửa đường log) sẽ âm thầm nạp lại một phiên đo cho ngày làm việc kế
# tiếp — thêm một kết nối 6.039 topic tranh với phiên ghi thật, cộng ~110 MB đĩa, vào
# một ngày không ai yêu cầu. Đã tồn tại thì để yên; muốn phiên đo mới thì xoá tay trước.
$measureTask = "dlck-ingester-measure"
if (Get-ScheduledTask -TaskName $measureTask -ErrorAction SilentlyContinue) {
    $nrt = (Get-ScheduledTaskInfo -TaskName $measureTask).NextRunTime
    Write-Host "  = $measureTask đã tồn tại (mốc kế: $nrt) — GIỮ NGUYÊN, không nạp lại."
    Write-Host "    Muốn phiên đo mới: Unregister-ScheduledTask -TaskName $measureTask -Confirm:`$false"
} else {
    Write-Host "Đăng ký phiên đo song song (một lần, ngày làm việc kế tiếp):"
    Register-DlckTask -TaskName $measureTask -AtTime "08:30" -ModuleArgs "ingester --measure" `
                      -LogFile "ingester-measure.log" -Once
}
Assert-TaskCommand -TaskName $measureTask -MustContain "python -m ingester --measure "

Write-Host "`nĐã kiểm lệnh của cả 7 task. Xem lại bất cứ lúc nào:"
Write-Host '  Get-ScheduledTask -TaskName "dlck-*" | % { $_.TaskName + " -> " + $_.Actions[0].Arguments }'
Write-Host "`n⚠️ Task chạy với tài khoản đang đăng nhập (Interactive). Muốn chạy cả khi"
Write-Host "   không đăng nhập, đăng ký lại bằng quyền admin với -LogonType S4U."
