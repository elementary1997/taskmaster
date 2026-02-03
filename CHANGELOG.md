# Changelog

All notable changes to this project will be documented in this file.


## [1.0.2] - 2026-02-02

### Fixed
- **PyInstaller Compatibility**:
    - Исправлена ошибка `Failed to import encodings module` на новых ПК без установленного Python.
    - Добавлены все необходимые модули стандартной библиотеки (encodings, urllib, http, ssl и др.).
    - Исправлена ошибка `base_library.zip` при проверке обновлений.
    - Улучшена стабильность запуска с помощью `bootloader-ignore-signals`.
- **Error Handling**:
    - Добавлена корректная обработка ошибок PyInstaller при проверке обновлений.
    - Улучшены сообщения об ошибках для пользователя.

### Improved
- **Notification Dialog**:
    - Формат даты изменен на DD.MM.YYYY (вместо YYYY-MM-DD) для лучшей читаемости.
    - Добавлена возможность открывать задачи по клику для просмотра полной информации.
    - Уменьшен размер окна уведомлений (320x400 вместо 400x500) для более компактного отображения.
    - Уменьшен размер шрифта: заголовок задачи 10pt (Medium), дата 8pt — соответствует главному окну.
    - Кнопка "Очистить уведомления" теперь очищает список задач в окне, не закрывая его.
    - После очистки уведомления не появляются повторно до следующего запуска программы (или до появления новых просроченных задач).
    - Окно уведомлений теперь "прилипает" к иконке уведомлений и автоматически обновляет позицию при перемещении главного окна.
    - Добавлен hover-эффект для карточек задач в окне уведомлений.

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
