# Changelog

All notable changes to this project will be documented in this file.


## [1.0.1] - 2026-01-30

### Fixed
- **Theme Consistency**:
    - Focus borders on input fields and dropdowns now correctly update to the active theme color immediately.
    - Fixed an issue where separator lines and section headers retained colors from the previous theme.
    - Bottom bar buttons (Help, Settings, Tools) now properly reflect theme colors (borders and hover states).
- **UI/UX Improvements**:
    - **Dropdown Readability**: Fixed transparency issues in the Priority dropdown where text overlapping with the background, and ensured text is readable in all themes.
    - **Popup Menu Boundaries**: "Filters" and "Theme" menus now automatically adjust their position to stay within the main window boundaries.
    - **Startup**: Fixed a bug where style corrections were applied only after switching themes, not on initial launch.

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
