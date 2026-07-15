-- ============================================================
--  GitHub Heatmap Calendar  -  Lua Controller  (v5 multi-click)
--
--  Behavior:
--  * Every day starts at 0 clicks (off/transparent).
--  * ONLY TODAY can be clicked. Each click increases the count
--    by 1 (up to maxClicksPerDay). Clicking past max resets to 0.
--  * Cell color saturation scales proportionally with click count:
--    0 clicks = off, max clicks = darkest green.
--  * maxClicksPerDay is configurable (default 4), stored in settings.txt.
--  * Click counts persist in toggledDays.txt (absolute path via CURRENTPATH).
--  * Night mode + Minimal mode + ClickThrough persist in settings.txt.
--  * Day/month rollover auto-detected; calendar rebuilds at midnight.
-- ============================================================

-- ---------- Layout (MUST match calendar.ini) ----------
local CELL_SIZE = 46
local CELL_GAP  = 4
local GRID_X    = 18
local GRID_Y    = 72
local WIDGET_W  = 380
local WIDGET_H_FULL    = 430
local WIDGET_H_MINIMAL = 374

-- ---------- Image file names ----------
-- We generate 8 saturation levels (1=lightest, 8=darkest) for each theme.
-- Lua picks which level to show based on count/maxClicks ratio.
local NUM_LEVELS = 8

local function levelImg(level, night)
  local prefix = night and 'cellLevelDark' or 'cellLevel'
  return prefix .. level .. '.png'
end

local function offImg(night)
  return night and 'cellOffDark.png' or 'cellOff.png'
end

local function emptyImg(night)
  return night and 'cellEmptyDark.png' or 'cellEmpty.png'
end

local function borderImg(night)
  return night and 'todayBorderDark.png' or 'todayBorder.png'
end

local monthNames = {
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
}

-- ---------- Runtime state ----------
local state = {
  cells          = {},
  todayCellIndex = 0,
  nightMode      = false,
  minimalMode    = false,
  clickThrough   = false,
  maxClicks      = 4,       -- configurable via settings + menu
  initialized    = false,
  dayCounts      = {},       -- map: "YYYY-MM-DD" = click count (1..maxClicks)
  _lastDay       = nil,
  _lastMonth     = nil,
}

-- ---------- Persistence file paths (absolute) ----------
local DATA_FILE     = nil  -- set in Initialize() via SKIN:GetVariable
local SETTINGS_FILE = nil

-- ---------- Logging ----------
local function log(msg)
  if SKIN then SKIN:Bang('!Log', tostring(msg), 'INFO') end
end
local function logErr(msg)
  if SKIN then SKIN:Bang('!Log', tostring(msg), 'ERROR') end
end

-- ---------- Date helpers ----------
local function dateKey(year, month, day)
  return string.format('%04d-%02d-%02d', year, month, day)
end

-- ---------- Map click count to saturation level (1..NUM_LEVELS) ----------
local function countToLevel(count, maxClicks)
  if count <= 0 then return 0 end
  if maxClicks <= 0 then maxClicks = 1 end
  -- Proportional: count=1 -> level 1, count=maxClicks -> level NUM_LEVELS
  local level = math.ceil((count / maxClicks) * NUM_LEVELS)
  if level < 1 then level = 1 end
  if level > NUM_LEVELS then level = NUM_LEVELS end
  return level
end

-- ---------- Persistence: day counts ----------
local function LoadDayCounts()
  state.dayCounts = {}
  if not DATA_FILE then return end
  local file = io.open(DATA_FILE, 'r')
  if not file then
    log('LoadDayCounts: no data file yet (first run)')
    return
  end
  local count = 0
  for line in file:lines() do
    line = line:gsub('[%s\r\n]', '')
    if #line >= 10 then
      -- New format: "YYYY-MM-DD:N" or old format: "YYYY-MM-DD"
      local key, num = line:match('^(%d%d%d%d%-%d%d%-%d%d):?(%d*)$')
      if key then
        local n = tonumber(num)
        if n and n > 0 then
          state.dayCounts[key] = n
        elseif #num == 0 then
          -- Old format (no colon) = 1 click
          state.dayCounts[key] = 1
        end
        count = count + 1
      end
    end
  end
  file:close()
  log('LoadDayCounts: loaded ' .. count .. ' day(s) with click data')
end

local function SaveDayCounts()
  if not DATA_FILE then return end
  local keys = {}
  for k, _ in pairs(state.dayCounts) do
    table.insert(keys, k)
  end
  table.sort(keys)
  local file = io.open(DATA_FILE, 'w')
  if not file then
    logErr('SaveDayCounts: cannot write to ' .. DATA_FILE)
    return
  end
  for _, k in ipairs(keys) do
    file:write(k .. ':' .. tostring(state.dayCounts[k]) .. '\n')
  end
  file:close()
  log('SaveDayCounts: saved ' .. #keys .. ' day(s)')
end

-- ---------- Persistence: settings ----------
local function LoadSettings()
  if not SETTINGS_FILE then return end
  local file = io.open(SETTINGS_FILE, 'r')
  if not file then
    log('LoadSettings: no settings file yet (first run)')
    return
  end
  for line in file:lines() do
    line = line:gsub('[%s\r\n]', '')
    local key, val = line:match('^(%w+)=(%w+)$')
    if key and val then
      if key == 'nightMode' then
        state.nightMode = (val == '1' or val == 'true')
      elseif key == 'minimalMode' then
        state.minimalMode = (val == '1' or val == 'true')
      elseif key == 'clickThrough' then
        state.clickThrough = (val == '1' or val == 'true')
      elseif key == 'maxClicks' then
        local n = tonumber(val)
        if n and n >= 1 then
          state.maxClicks = n
        end
      end
    end
  end
  file:close()
  log('LoadSettings: nightMode=' .. tostring(state.nightMode) ..
      ' minimalMode=' .. tostring(state.minimalMode) ..
      ' clickThrough=' .. tostring(state.clickThrough) ..
      ' maxClicks=' .. tostring(state.maxClicks))
end

local function SaveSettings()
  if not SETTINGS_FILE then return end
  local file = io.open(SETTINGS_FILE, 'w')
  if not file then
    logErr('SaveSettings: cannot write to ' .. SETTINGS_FILE)
    return
  end
  file:write('nightMode=' .. (state.nightMode and '1' or '0') .. '\n')
  file:write('minimalMode=' .. (state.minimalMode and '1' or '0') .. '\n')
  file:write('clickThrough=' .. (state.clickThrough and '1' or '0') .. '\n')
  file:write('maxClicks=' .. tostring(state.maxClicks) .. '\n')
  file:close()
  log('SaveSettings: maxClicks=' .. tostring(state.maxClicks))
end

-- ---------- Apply cell image based on click count ----------
local function ApplyCellImage(i)
  local cell = state.cells[i]
  if not cell then return end

  local imgName
  if not cell.isCurrentMonth then
    imgName = emptyImg(state.nightMode)
  else
    local now = os.date('*t')
    local key = dateKey(now.year, now.month, tonumber(cell.day))
    local count = state.dayCounts[key] or 0
    if count > 0 then
      local level = countToLevel(count, state.maxClicks)
      imgName = levelImg(level, state.nightMode)
    else
      imgName = offImg(state.nightMode)
    end
  end

  if not imgName then return end
  SKIN:Bang('!SetOption', 'Cell' .. i, 'ImageName', '#@#' .. imgName)
  SKIN:Bang('!UpdateMeter', 'Cell' .. i)
end

-- ---------- Position today border overlay ----------
local function PositionTodayBorder()
  if state.todayCellIndex == 0 then
    SKIN:Bang('!SetOption', 'TodayBorder', 'Hidden', '1')
    SKIN:Bang('!UpdateMeter', 'TodayBorder')
    return
  end

  local i = state.todayCellIndex
  local col = (i - 1) % 7
  local row = math.floor((i - 1) / 7)
  local x   = GRID_X + col * (CELL_SIZE + CELL_GAP)
  local y   = GRID_Y + row * (CELL_SIZE + CELL_GAP)

  SKIN:Bang('!SetOption', 'TodayBorder', 'ImageName', '#@#' .. borderImg(state.nightMode))
  SKIN:Bang('!SetOption', 'TodayBorder', 'X', tostring(x))
  SKIN:Bang('!SetOption', 'TodayBorder', 'Y', tostring(y))
  SKIN:Bang('!SetOption', 'TodayBorder', 'Hidden', '0')
  SKIN:Bang('!UpdateMeter', 'TodayBorder')
end

-- ---------- Show/hide meters for minimal mode ----------
local function ApplyMinimalMode()
  local hideFlag = state.minimalMode and '1' or '0'
  local hideMeters = {
    'MonthTitle', 'TodayBadge',
    'Weekday0', 'Weekday1', 'Weekday2', 'Weekday3',
    'Weekday4', 'Weekday5', 'Weekday6',
    'NightModeButton', 'NightModeButtonText',
    'IlluminateButton', 'IlluminateButtonText',
    'LegendLabelLess', 'LegendOff', 'LegendOn', 'LegendLabelMore',
  }
  for _, m in ipairs(hideMeters) do
    SKIN:Bang('!SetOption', m, 'Hidden', hideFlag)
  end

  -- Day numbers stay VISIBLE in minimal mode

  -- Background: HIDE in minimal mode, show in normal mode
  if state.minimalMode then
    SKIN:Bang('!SetOption', 'Background', 'Hidden', '1')
  else
    SKIN:Bang('!SetOption', 'Background', 'Hidden', '0')
    local bg, stroke
    if state.nightMode then
      bg     = '13,17,23'
      stroke = '48,54,61'
    else
      bg     = '255,255,255'
      stroke = '208,215,222'
    end
    SKIN:Bang('!SetOption', 'Background', 'Shape',
      'Rectangle 0,0,' .. WIDGET_W .. ',' .. WIDGET_H_FULL .. ',12 | Fill Color ' .. bg ..
      ' | StrokeWidth 1 | Stroke Color ' .. stroke)
  end
  SKIN:Bang('!UpdateMeter', 'Background')
end

-- ---------- Update UI colors based on night mode ----------
local function ApplyThemeColors()
  if state.nightMode then
    SKIN:Bang('!SetOption', 'MonthTitle', 'FontColor', '230,237,243')
    SKIN:Bang('!SetOption', 'TodayBadge', 'FontColor', '88,166,255')
    for i = 0, 6 do
      SKIN:Bang('!SetOption', 'Weekday' .. i, 'FontColor', '139,148,158')
    end
    SKIN:Bang('!SetOption', 'LegendLabelLess', 'FontColor', '139,148,158')
    SKIN:Bang('!SetOption', 'LegendLabelMore', 'FontColor', '139,148,158')
    SKIN:Bang('!SetOption', 'NightModeButtonText', 'Text', 'Light Mode')
    SKIN:Bang('!SetOption', 'NightModeButton', 'Shape',
      'Rectangle 18,388,168,32,8 | Fill Color 48,54,61 | StrokeWidth 1 | Stroke Color 139,148,158')
    SKIN:Bang('!SetOption', 'NightModeButtonText', 'FontColor', '230,237,243')
    SKIN:Bang('!SetOption', 'IlluminateButton', 'Shape',
      'Rectangle 194,388,168,32,8 | Fill Color 63,218,122 | StrokeWidth 0')
    SKIN:Bang('!SetOption', 'IlluminateButtonText', 'FontColor', '13,17,23')
    -- Update illuminate button text to show today's count
    local now = os.date('*t')
    local key = dateKey(now.year, now.month, now.day)
    local todayCount = state.dayCounts[key] or 0
    SKIN:Bang('!SetOption', 'IlluminateButtonText', 'Text',
      'Today: ' .. todayCount .. '/' .. state.maxClicks)
  else
    SKIN:Bang('!SetOption', 'MonthTitle', 'FontColor', '31,35,40')
    SKIN:Bang('!SetOption', 'TodayBadge', 'FontColor', '9,105,218')
    for i = 0, 6 do
      SKIN:Bang('!SetOption', 'Weekday' .. i, 'FontColor', '101,109,118')
    end
    SKIN:Bang('!SetOption', 'LegendLabelLess', 'FontColor', '101,109,118')
    SKIN:Bang('!SetOption', 'LegendLabelMore', 'FontColor', '101,109,118')
    SKIN:Bang('!SetOption', 'NightModeButtonText', 'Text', 'Night Mode')
    SKIN:Bang('!SetOption', 'NightModeButton', 'Shape',
      'Rectangle 18,388,168,32,8 | Fill Color 240,246,252 | StrokeWidth 1 | Stroke Color 208,215,222')
    SKIN:Bang('!SetOption', 'NightModeButtonText', 'FontColor', '31,35,40')
    SKIN:Bang('!SetOption', 'IlluminateButton', 'Shape',
      'Rectangle 194,388,168,32,8 | Fill Color 9,105,218 | StrokeWidth 0')
    SKIN:Bang('!SetOption', 'IlluminateButtonText', 'FontColor', '255,255,255')
    local now = os.date('*t')
    local key = dateKey(now.year, now.month, now.day)
    local todayCount = state.dayCounts[key] or 0
    SKIN:Bang('!SetOption', 'IlluminateButtonText', 'Text',
      'Today: ' .. todayCount .. '/' .. state.maxClicks)
  end

  -- Today badge text
  local badgeText = 'Today'
  if state.todayCellIndex > 0 and state.cells[state.todayCellIndex] then
    local now = os.date('*t')
    local key = dateKey(now.year, now.month, now.day)
    local todayCount = state.dayCounts[key] or 0
    badgeText = 'Day ' .. state.cells[state.todayCellIndex].day ..
                ' (' .. todayCount .. '/' .. state.maxClicks .. ')'
  end
  SKIN:Bang('!SetOption', 'TodayBadge', 'Text', badgeText)

  -- Cell text colors
  for i = 1, 42 do
    local cell = state.cells[i]
    if cell then
      local fc
      if state.nightMode then
        fc = cell.isCurrentMonth and '230,237,243' or '139,148,158'
      else
        fc = cell.isCurrentMonth and '31,35,40' or '101,109,118'
      end
      SKIN:Bang('!SetOption', 'CellText' .. i, 'FontColor', fc)
      SKIN:Bang('!UpdateMeter', 'CellText' .. i)
    end
  end

  -- Cell images
  for i = 1, 42 do
    ApplyCellImage(i)
  end

  -- Legend (Off | Full)
  SKIN:Bang('!SetOption', 'LegendOff', 'ImageName',
    '#@#' .. (state.nightMode and 'cellOffDark.png' or 'cellOff.png'))
  SKIN:Bang('!SetOption', 'LegendOn', 'ImageName',
    '#@#' .. levelImg(NUM_LEVELS, state.nightMode))
  SKIN:Bang('!UpdateMeter', 'LegendOff')
  SKIN:Bang('!UpdateMeter', 'LegendOn')

  ApplyMinimalMode()

  SKIN:Bang('!UpdateMeter', 'MonthTitle')
  SKIN:Bang('!UpdateMeter', 'TodayBadge')
  for i = 0, 6 do SKIN:Bang('!UpdateMeter', 'Weekday' .. i) end
  SKIN:Bang('!UpdateMeter', 'LegendLabelLess')
  SKIN:Bang('!UpdateMeter', 'LegendLabelMore')
  SKIN:Bang('!UpdateMeter', 'NightModeButton')
  SKIN:Bang('!UpdateMeter', 'NightModeButtonText')
  SKIN:Bang('!UpdateMeter', 'IlluminateButton')
  SKIN:Bang('!UpdateMeter', 'IlluminateButtonText')
  PositionTodayBorder()
  SKIN:Bang('!Redraw')
end

-- ---------- Build the 6x7 calendar grid ----------
function BuildCalendar()
  log('BuildCalendar: START')

  local now   = os.date('*t')
  local year  = now.year
  local month = now.month
  local today = now.day

  local firstInfo = os.date('*t', os.time({year=year, month=month, day=1}))
  local firstWday = firstInfo.wday

  local lastDayInfo = os.date('*t', os.time({year=year, month=month+1, day=0}))
  local daysInMonth = lastDayInfo.day

  state.cells          = {}
  state.todayCellIndex = 0

  for i = 1, 42 do
    local dayNum         = i - firstWday + 1
    local isCurrentMonth = (dayNum >= 1 and dayNum <= daysInMonth)
    local isToday        = isCurrentMonth and (dayNum == today)
    state.cells[i] = {
      day             = isCurrentMonth and tostring(dayNum) or '',
      isCurrentMonth = isCurrentMonth,
      isToday         = isToday,
    }
    if isToday then
      state.todayCellIndex = i
    end
  end
  log('BuildCalendar: todayCellIndex=' .. state.todayCellIndex)

  state._lastDay   = today
  state._lastMonth = month

  for i = 1, 42 do
    SKIN:Bang('!SetOption', 'CellText' .. i, 'Text', state.cells[i].day)
  end

  local title = monthNames[month] .. ' ' .. year
  SKIN:Bang('!SetOption', 'MonthTitle', 'Text', title)

  ApplyThemeColors()
  log('BuildCalendar: DONE - title="' .. title .. '"')
end

-- ---------- Rainmeter entry points ----------

function Initialize()
  log('========================================')
  log('Initialize: START')

  -- Get absolute path to skin folder via Rainmeter variable
  -- #CURRENTPATH# includes trailing backslash on Windows
  local skinPath = SKIN:GetVariable('CURRENTPATH')
  if skinPath then
    DATA_FILE     = skinPath .. 'toggledDays.txt'
    SETTINGS_FILE = skinPath .. 'settings.txt'
  else
    -- Fallback: try relative (may not persist correctly)
    DATA_FILE     = 'toggledDays.txt'
    SETTINGS_FILE = 'settings.txt'
    logErr('Initialize: SKIN:GetVariable(\"CURRENTPATH\") returned nil! Using relative paths.')
  end
  log('Initialize: DATA_FILE = ' .. tostring(DATA_FILE))
  log('Initialize: SETTINGS_FILE = ' .. tostring(SETTINGS_FILE))

  LoadSettings()
  LoadDayCounts()

  -- Apply click-through on startup if it was saved as ON
  if state.clickThrough then
    SKIN:Bang('!SetOption', 'Rainmeter', 'ClickThrough', '1')
  end

  local ok, err = pcall(BuildCalendar)
  if not ok then
    logErr('Initialize ERROR: ' .. tostring(err))
  else
    state.initialized = true
    log('Initialize: SUCCESS')
  end
  log('========================================')
end

function Update()
  if state.initialized then
    local now = os.date('*t')
    if state._lastDay ~= now.day or state._lastMonth ~= now.month then
      log('Update: day/month changed, rebuilding calendar')
      pcall(BuildCalendar)
    end
  end
  return 0
end

-- ---------- Click a day (by cell index) ----------
-- HABITS MODE: only today's cell can be clicked.
-- Each click increments count. Past max -> resets to 0.
function ToggleDay(cellIndex)
  if not state.initialized then return end
  local cell = state.cells[cellIndex]
  if not cell or not cell.isCurrentMonth then
    log('ToggleDay: ignored (not current month)')
    return
  end
  if not cell.isToday then
    log('ToggleDay: ignored (day ' .. cell.day .. ' is not today)')
    return
  end

  local now = os.date('*t')
  local key = dateKey(now.year, now.month, tonumber(cell.day))
  local current = state.dayCounts[key] or 0

  if current >= state.maxClicks then
    -- Already at max -> reset to 0
    state.dayCounts[key] = nil
    log('ToggleDay: ' .. key .. ' reset to 0 (was at max ' .. state.maxClicks .. ')')
  else
    state.dayCounts[key] = current + 1
    log('ToggleDay: ' .. key .. ' now ' .. (current + 1) .. '/' .. state.maxClicks)
  end

  SaveDayCounts()
  ApplyCellImage(cellIndex)

  -- Update today badge + button text
  local newCount = state.dayCounts[key] or 0
  SKIN:Bang('!SetOption', 'TodayBadge', 'Text',
    'Day ' .. cell.day .. ' (' .. newCount .. '/' .. state.maxClicks .. ')')
  SKIN:Bang('!SetOption', 'IlluminateButtonText', 'Text',
    'Today: ' .. newCount .. '/' .. state.maxClicks)
  SKIN:Bang('!UpdateMeter', 'TodayBadge')
  SKIN:Bang('!UpdateMeter', 'IlluminateButtonText')
  SKIN:Bang('!Redraw')
end

-- ---------- Toggle today (button) ----------
function ToggleIlluminate()
  if state.todayCellIndex > 0 then
    ToggleDay(state.todayCellIndex)
  else
    logErr('ToggleToday: no today cell found')
  end
end

-- ---------- Toggle night mode ----------
function ToggleNightMode()
  state.nightMode = not state.nightMode
  log('ToggleNightMode: ' .. (state.nightMode and 'DARK' or 'LIGHT'))
  SaveSettings()
  ApplyThemeColors()
end

-- ---------- Toggle minimal mode ----------
function ToggleMinimalMode()
  state.minimalMode = not state.minimalMode
  log('ToggleMinimalMode: ' .. (state.minimalMode and 'ON' or 'OFF'))
  SaveSettings()
  ApplyThemeColors()
end

-- ---------- Toggle click-through ----------
function ToggleClickThrough()
  state.clickThrough = not state.clickThrough
  log('ToggleClickThrough: ' .. (state.clickThrough and 'ON' or 'OFF'))
  if state.clickThrough then
    SKIN:Bang('!SetOption', 'Rainmeter', 'ClickThrough', '1')
  else
    SKIN:Bang('!SetOption', 'Rainmeter', 'ClickThrough', '0')
  end
  SaveSettings()
end

-- ---------- Set max clicks per day ----------
function SetMaxClicks(n)
  n = tonumber(n)
  if not n or n < 1 then n = 1 end
  if n > 20 then n = 20 end  -- sanity cap
  state.maxClicks = n
  log('SetMaxClicks: ' .. n)
  SaveSettings()
  ApplyThemeColors()
end

-- ---------- Position presets ----------
function PositionTopRight()
  SKIN:Bang('!Move', '#SCREENAREAWIDTH#', '0')
end
function PositionBottomRight()
  SKIN:Bang('!Move', '#SCREENAREAWIDTH#', '#SCREENAREAHEIGHT#')
end
function PositionTopLeft()
  SKIN:Bang('!Move', '0', '0')
end
function PositionBottomLeft()
  SKIN:Bang('!Move', '0', '#SCREENAREAHEIGHT#')
end

-- ---------- Refresh ----------
function Refresh()
  log('Refresh')
  LoadSettings()
  LoadDayCounts()
  pcall(BuildCalendar)
end
