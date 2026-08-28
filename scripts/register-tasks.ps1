# Đăng ký Task Scheduler cho lát cắt ingester + OMO (spec 2026-08-26 §3.8/§4.5).
# Chạy: pwsh scripts/register-tasks.ps1                    (mặc định Interactive)
#       pwsh scripts/register-tasks.ps1 -LogonType S4U     (CẦN CỬA SỔ ADMIN)
# Chạy lại được — ghi đè task cùng tên.
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

param(
    # S4U = chạy cả khi không đăng nhập, KHÔNG hiện cửa sổ cmd (service-topology §5).
    # Mặc định Interactive để chạy không tham số giữ nguyên hành vi cũ.
    # ⚠️ S4U đòi cửa sổ Run as Administrator — không có quyền thì Register-ScheduledTask
    #    ném "Access is denied", task giữ nguyên đăng ký cũ.
    [ValidateSet("Interactive", "S4U", "Password", "InteractiveOrPassword")]
    [string] $LogonType = "Interactive"
)

$repo    = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$logDir  = Join-Path (Split-Path $repo -Parent) "dlck-runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$uv = (Get-Command uv -ErrorAction Stop).Source
# UserId/RunLevel giữ đúng cái 7 task đang mang (kiểm 2026-08-28: tuanb / Limited) —
# lượt này CHỈ đổi LogonType, không nhân tiện đổi quyền chạy.
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType $LogonType `
                 -RunLevel Limited

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
        -Settings $settings -Principal $principal -Force | Out-Null
    # Cùng bài học §3.5 như Assert-TaskCommand, áp cho principal: đăng ký "thành công"
    # KHÔNG chứng minh LogonType đã đổi. Kiểm ngay trong hàm nên không task nào lọt.
    Assert-TaskLogonType -TaskName $TaskName -Expected $LogonType
    Write-Host ("  + {0,-24} {1,-16}  ->  python -m {2}" -f $TaskName, $AtTime, $ModuleArgs)
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

function Assert-TaskLogonType {
    <#  Nghiệm thu: soi PRINCIPAL thật của task, không tin lệnh vừa gọi đã có tác dụng.  #>
    param([string] $TaskName, [string] $Expected)
    $actual = (Get-ScheduledTask -TaskName $TaskName).Principal.LogonType
    if ("$actual" -ne $Expected) {
        throw "Task $TaskName đăng ký SAI LogonType — xin '$Expected', thật '$actual'."
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

# Phiên đo song song HẰNG NGÀY: bắt frame THÔ ra JSONL trong khi phiên ghi chạy
# (quyết định 2026-08-27, roadmap §2.1). Hai việc không cơ chế nào khác làm:
# (1) lưới an toàn dựng-lại-được cho chỗ hở hàng đợi `pending` không trần — cho tới
#     khi lát tràn-ra-đĩa xong, ngày nào không có bản thô là ngày đó mất là mất hẳn;
# (2) đường nghiệm thu "không mất dòng nào" bằng SỐ — bản đo là đếm độc lập với kho.
# Chi phí ~93 MB gzip/ngày; chính sách giữ 30 ngày nằm trong chính job đo
# (`prune_old`, backend/ingester/measure.py) nên không cần task dọn riêng.
# Trước đây task này là MỘT LẦN kèm chốt "đã tồn tại thì giữ nguyên" — chốt đó dựng
# cho task một-lần (chạy lại script sẽ âm thầm nạp thêm một phiên đo); task hằng ngày
# thì đăng ký đè idempotent như mọi task khác, chốt đã bỏ.
$measureTask = "dlck-ingester-measure"
Write-Host "Đăng ký phiên đo song song (hằng ngày làm việc, chạy cạnh phiên ghi):"
Register-DlckTask -TaskName $measureTask -AtTime "08:30" -ModuleArgs "ingester --measure" `
                  -LogFile "ingester-measure.log"
Assert-TaskCommand -TaskName $measureTask -MustContain "python -m ingester --measure "

Write-Host "`nĐã kiểm lệnh của cả 7 task. Xem lại bất cứ lúc nào:"
Write-Host '  Get-ScheduledTask -TaskName "dlck-*" | % { $_.TaskName + " -> " + $_.Actions[0].Arguments }'
if ($LogonType -eq "S4U") {
    Write-Host "`n✅ Cả 7 task đăng ký S4U (đã soi Principal thật từng task, không chỉ soi lệnh):"
    Write-Host "   chạy cả khi không đăng nhập, KHÔNG hiện cửa sổ cmd để bấm nhầm."
    Write-Host "   ⚠️ Script đăng ký lại CẢ BẢY — task nào đang cố ý Disabled sẽ sống lại BẬT."
    Write-Host '      Tắt lại: Get-ScheduledTask -TaskName "dlck-omo-*" | Disable-ScheduledTask'
} else {
    Write-Host "`n⚠️ Task chạy với tài khoản đang đăng nhập (Interactive). Muốn chạy cả khi"
    Write-Host "   không đăng nhập, đăng ký lại bằng quyền admin với -LogonType S4U."
    Write-Host "   Cửa sổ cmd hiện ra cũng vì Interactive — bấm nhầm X là giết tiến trình."
    Write-Host "   Ba hệ quả và cửa sổ đăng ký lại an toàn: docs/20-design/service-topology.md §5."
}
