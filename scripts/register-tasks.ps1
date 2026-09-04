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
    # Chỉ hai giá trị: script không truyền -User/-Password nên Password/InteractiveOrPassword
    # không thể hoạt động — nhận chúng là hứa một thứ không làm được (§4.4.2).
    [ValidateSet("Interactive", "S4U")]
    [string] $LogonType = "Interactive"
)

$repo    = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$logDir  = Join-Path (Split-Path $repo -Parent) "dlck-runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$uv = (Get-Command uv -ErrorAction Stop).Source
# Chụp trạng thái TRƯỚC khi -Force đè lên, để cuối script báo đúng task nào bị bật lại.
$script:disabledBefore = @(Get-ScheduledTask -TaskName 'dlck-*' -ErrorAction SilentlyContinue |
                           Where-Object { $_.State -eq 'Disabled' } | ForEach-Object TaskName)
# RunLevel giữ đúng cái 7 task đang mang (kiểm 2026-08-28: Limited) — lượt này CHỈ
# đổi LogonType, không nhân tiện đổi quyền chạy.
#
# 🔴 UserId PHẢI qualified "DOMAIN\user", KHÔNG được để tên trần.
# Get-ScheduledTask HIỂN THỊ UserId là "tuanb", nhưng dạng hiển thị KHÁC dạng nhận
# vào: Register-ScheduledTask với tên trần ném "The parameter is incorrect.
# (15,8):UserId:". Đo thật 2026-08-28 bằng probe trên task rác, cả ba dạng:
#     tuanb                      -> FAIL
#     TUANB\tuanb                -> OK (S4U đăng ký được)
#     S-1-5-21-…-1001 (SID)      -> FAIL
# Và lỗi này KHÔNG chỉ dính S4U — Interactive + tên trần cũng FAIL y hệt. Bản script
# cũ thoát được vì nó không truyền -Principal nên chẳng phải phân giải UserId nào.
$principalUser = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $principalUser `
                 -LogonType $LogonType -RunLevel Limited

function Register-DlckTask {
    param(
        [Parameter(Mandatory)][string] $TaskName,
        [Parameter(Mandatory)][string] $AtTime,      # "HH:mm"
        [Parameter(Mandatory)][string] $ModuleArgs,  # ví dụ "etl omo"
        [Parameter(Mandatory)][string] $LogFile,
        # Mặc định ngày làm việc. Task backfill giá chạy thứ 7 (kích hoạt tay buổi tối thì không cần trigger).
        [string[]] $DaysOfWeek = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"),
        # 12 giờ đủ cho mọi job trong ngày; backfill giá chạy trọn cuối tuần cần 3 ngày.
        [timespan] $ExecutionTimeLimit = (New-TimeSpan -Hours 12)
    )
    # Interactive: cửa sổ cmd hiện ra trong lúc job chạy — tiêu đề = tên task và một dòng in job + log,
    # để nhìn thanh taskbar là biết task nào đang chạy (quyết định chủ dự án 2026-09-04: thích thấy cửa sổ
    # hơn là phải đăng ký S4U trong cửa sổ admin mỗi lần thêm task). Output thật vẫn đi vào file log.
    # Dòng echo để ASCII không dấu: cmd.exe hiển thị theo codepage OEM, tiếng Việt có dấu sẽ vỡ.
    # Nút X bị chính job khoá lúc khởi động (core/console.py) — dừng bằng Ctrl+C hoặc Stop-ScheduledTask.
    # DLCK_LOCK_CONSOLE=1 chỉ đặt ở đây: chạy tay từ terminal thì job không khoá nút X của terminal đó.
    $inner = 'title {4} && echo [{4}] python -m {2} -- nut X bi khoa khi job chay, dung bang Ctrl+C hoac Stop-ScheduledTask {4} -- log: {3} && cd /d "{0}" && set PYTHONIOENCODING=utf-8 && set DLCK_LOCK_CONSOLE=1 && "{1}" run python -m {2} >> "{3}" 2>&1' `
             -f $backend, $uv, $ModuleArgs, (Join-Path $logDir $LogFile), $TaskName
    $action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $inner"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DaysOfWeek -At $AtTime
    # StartWhenAvailable: máy ngủ/tắt qua giờ chạy thì chạy bù khi bật lại.
    # RestartCount/RestartInterval: tự khởi động lại khi tiến trình chết (spec §3.8).
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) `
                    -MultipleInstances IgnoreNew -ExecutionTimeLimit $ExecutionTimeLimit
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Force | Out-Null
    # Cùng bài học §3.5 như Assert-TaskCommand, áp cho principal: đăng ký "thành công"
    # KHÔNG chứng minh LogonType đã đổi. Kiểm ngay trong hàm nên không task nào lọt.
    Assert-TaskPrincipal -TaskName $TaskName -ExpectedLogonType $LogonType `
                         -ExpectedUserId $principalUser
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

function Assert-TaskPrincipal {
    <#  Nghiệm thu: soi PRINCIPAL thật của task, không tin lệnh vừa gọi đã có tác dụng.
        Soi CẢ HAI vế — LogonType lẫn danh tính chạy dưới quyền ai. Chỉ soi LogonType là
        bỏ sót đúng thứ lượt sửa này làm cho động: nếu cửa sổ admin được nâng quyền bằng
        MỘT TÀI KHOẢN KHÁC (UAC "over-the-shoulder"), `$env:USERNAME` là tài khoản admin
        đó, cả 7 task đăng ký dưới principal sai mà phép kiểm LogonType vẫn xanh — rồi
        ingester chạy trong session không có Docker Desktop của người dùng thật.
        So bằng SID chứ không so chuỗi: `Get-ScheduledTask` HIỂN THỊ UserId rút gọn
        ("TUANB	uanb" -> "tuanb"), so chuỗi sẽ đỏ oan.  #>
    param([string] $TaskName, [string] $ExpectedLogonType, [string] $ExpectedUserId)
    $p = (Get-ScheduledTask -TaskName $TaskName).Principal
    if ("$($p.LogonType)" -ne $ExpectedLogonType) {
        throw "Task $TaskName đăng ký SAI LogonType — xin '$ExpectedLogonType', thật '$($p.LogonType)'."
    }
    # Task LƯU UserId dạng rút gọn ("TUANB\tuanb" -> "tuanb"), mà tên trần KHÔNG dịch
    # được sang SID trên tài khoản Microsoft (đo 2026-08-28: "TUANB\tuanb" OK, "tuanb"
    # ném "Some or all identity references could not be translated"). Nên phải qualified
    # lại trước khi dịch — nếu không, chính guard này đổ ở giá trị nó phải đọc.
    $toSid = {
        param($n)
        if (-not ($n.Contains('\') -or $n.Contains('@'))) { $n = "$env:USERDOMAIN\$n" }
        try { (New-Object System.Security.Principal.NTAccount($n)).Translate(
                [System.Security.Principal.SecurityIdentifier]).Value } catch { $null }
    }
    $want = & $toSid $ExpectedUserId
    $got  = & $toSid $p.UserId
    if ($want -and $got) {
        if ($got -ne $want) {
            throw "Task $TaskName chạy dưới PRINCIPAL SAI — xin '$ExpectedUserId' ($want), thật '$($p.UserId)' ($got)."
        }
    }
    elseif ($p.UserId.Split('\')[-1] -ine $ExpectedUserId.Split('\')[-1]) {
        # Đường lùi khi không dịch được SID cả hai phía: so tên lá, vẫn hơn không kiểm gì.
        throw "Task $TaskName chạy dưới PRINCIPAL SAI — xin '$ExpectedUserId', thật '$($p.UserId)' (SID không dịch được, so theo tên)."
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

Write-Host "Đăng ký screener (15:20 ngày làm việc — sau khi ingester ghi xong 15:05, tránh 15:30 của OMO):"
Register-DlckTask -TaskName "dlck-screener" -AtTime "15:20" -ModuleArgs "etl screener" -LogFile "screener.log"
Assert-TaskCommand -TaskName "dlck-screener" -MustContain "python -m etl screener"

Write-Host "Đăng ký events (18:10 ngày làm việc — sau phiên, sau screener 15:20, và tránh 18:00 của OMO):"
Register-DlckTask -TaskName "dlck-events" -AtTime "18:10" -ModuleArgs "etl events" -LogFile "events.log"
# -MustNotContain là chốt chặn thật: task tự động KHÔNG BAO GIỜ được mang cờ cho phép
# đẻ issuer tối thiểu hàng loạt — lượt đó phải chạy tay có người nhìn.
Assert-TaskCommand -TaskName "dlck-events" -MustContain "python -m etl events" -MustNotContain "--accept-new"

Write-Host "Đăng ký price (15:40 ngày làm việc — sau screener 15:20 và OMO 15:30; ~45 phút tuần tự, xong trước 18:00 của OMO):"
Register-DlckTask -TaskName "dlck-price" -AtTime "15:40" -ModuleArgs "etl price" -LogFile "price.log"
# -MustNotContain: task tự động KHÔNG BAO GIỜ chạy backfill (25–40 giờ, chạy tay ngoài giờ có người nhìn).
Assert-TaskCommand -TaskName "dlck-price" -MustContain "python -m etl price" -MustNotContain "--backfill"

Write-Host "Đăng ký price-backfill (thứ 7 00:05 — lùi trọn lịch sử giá ~12,5 năm, ~20 giờ gọi tuần tự; chạy tới 08:45 thứ 2 hoặc tới khi hết vòng):"
# --stop-before-open: hạn là 08:45 của ngày giao dịch kế tiếp, tính lúc job bắt đầu — nên kích hoạt TAY
# buổi tối bất kỳ (Start-ScheduledTask dlck-price-backfill) cũng tự dừng trước phiên sáng hôm sau.
# Con trỏ trong ops.etl_run nối các lượt; máy ngủ 02:00 giữa chừng thì job sống qua và chạy tiếp tới hạn.
# Hết vòng (pass_complete) thì lượt kế là VÒNG MỚI (làm mới toàn bộ chuỗi điều chỉnh) — cân nhắc tắt task
# sau vòng đầu nếu không muốn ~20 giờ gọi mỗi cuối tuần.
Register-DlckTask -TaskName "dlck-price-backfill" -AtTime "00:05" -DaysOfWeek Saturday `
                  -ModuleArgs "etl price --backfill --stop-before-open" -LogFile "price-backfill.log" `
                  -ExecutionTimeLimit (New-TimeSpan -Days 3)
Assert-TaskCommand -TaskName "dlck-price-backfill" -MustContain "python -m etl price --backfill --stop-before-open"

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

Write-Host "`nĐã kiểm lệnh của cả 11 task. Xem lại bất cứ lúc nào:"
Write-Host '  Get-ScheduledTask -TaskName "dlck-*" | % { $_.TaskName + " -> " + $_.Actions[0].Arguments }'
# Cảnh báo này KHÔNG phụ thuộc LogonType: `Register-ScheduledTask -Force` thay định
# nghĩa task ở MỌI lượt chạy, và New-ScheduledTaskSettingsSet không có cờ giữ trạng thái
# Disabled — nên lượt chạy mặc định (Interactive) cũng bật lại task đang cố ý tắt. Ca này
# đã xảy ra thật 2026-08-28 với 4 task OMO.
if ($script:disabledBefore.Count -gt 0) {
    Write-Host ("`n⚠️ {0} task ĐANG TẮT trước lượt này đã bị -Force bật lại: {1}" -f `
                $script:disabledBefore.Count, ($script:disabledBefore -join ", "))
    Write-Host '   Tắt lại nếu vẫn muốn giữ:  Get-ScheduledTask -TaskName "<tên>" | Disable-ScheduledTask'
}

if ($LogonType -eq "S4U") {
    Write-Host "`n✅ Cả 11 task đăng ký S4U (đã soi Principal thật từng task, không chỉ soi lệnh):"
    Write-Host "   chạy cả khi không đăng nhập, KHÔNG hiện cửa sổ cmd để bấm nhầm."
} else {
    Write-Host "`n⚠️ Task chạy với tài khoản đang đăng nhập (Interactive). Muốn chạy cả khi"
    Write-Host "   không đăng nhập, đăng ký lại bằng quyền admin với -LogonType S4U."
    Write-Host "   Cửa sổ cmd hiện ra cũng vì Interactive — bấm nhầm X là giết tiến trình."
    Write-Host "   Ba hệ quả và cửa sổ đăng ký lại an toàn: docs/20-design/service-topology.md §5."
}
