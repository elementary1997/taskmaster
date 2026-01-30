# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-01-30

### Added
- **Auto-Update System**: 
    - Full update cycle: notification -> download -> safe replacement of executable.
    - Automatic cleanup of old `.bak` files on the next launch.
    - Direct EXE downloading from GitHub releases.
- **Markdown Update Dialog**:
    - Beautifully formatted changelogs with headers, lists, and bold text support.
    - Integrated download progress bar and status notifications.
- **Task Filtering System**:
    - Compact search & filter button with a dropdown menu.
    - Added quick-access filters: **All Content**, **Active Tasks**, and Priority-based (� High, � Medium, 🟢 Low).
- **UX Improvements**:
    - Large drop zone (150px) for moving tasks from "Completed" back to "Active".
    - Fixed the "black box" tooltip issue; added rounded corners and theme-consistent colors.
    - Selection highlighting in priority level select.

### Fixed
- Fixed icon clipping in the filter dropdown menu.
- Corrected initialization order in UI setup preventing application crashes.

## [1.0.0] - 2026-01-30

### Added
- **Initial Release of Modern Task Manager**.
- **Core Features**:
    - Task creation with three priority levels (High, Medium, Low).
    - Pomodoro-style timer for each task.
    - Drag & drop functionality for task reordering and status changes.
    - "Completed Tasks" history section.
- **Dynamic Design**:
    - 5 built-in color themes (Blue, Green, Purple, Dark, Pink).
    - Window transparency and UI scaling adjustments.
    - Custom tray icon and background mode.
- **Smart Logic**:
    - Russian pluralization support for task counters.
    - Auto-collapsing/expanding sections.
- **Optimization**:
    - Highly optimized Windows executable size (~60MB).
    - Fast startup time (<2s).
