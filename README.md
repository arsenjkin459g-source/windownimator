![README](assets/readme_header.jpg)

# Windownimator 2.0

![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white) ![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white) ![Status Release](https://img.shields.io/badge/Status-v2.1.0-green?style=for-the-badge) ![GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)

> [!NOTE]
> **ОБНОВЛЕНИЕ: ВЕРСИЯ 2.1.0 (DISCORD RICH PRESENCE)**  
> Добавлена встроенная интеграция Discord Rich Presence, поддержка отслеживания названий проектов, кадров, времени работы и статуса стартового меню.

Windownimator — мощный графический редактор и движок для создания интерактивных анимаций из системных диалоговых окон Windows (`MessageBoxW`).

Окна перемещаются по виртуальному холсту по ключевым кадрам с поддержкой плавных математических функций сглаживания (easing), воспроизводят привязанные звуки и экспортируются в автономные `.exe` файлы.

![ВОЗМОЖНОСТИ](assets/features_header.jpg)

### Что нового в Windownimator 2.1.0:

- 🎮 **Интеграция Discord Rich Presence (RPC)**: Динамическое отображение статуса работы в вашем профиле Discord (имя проекта, количество кадров, окон и таймер активности).
- 🚀 **Приветственный мастер старта (`WelcomeDialog`)**: Быстрый запуск для создания новой анимации или открытия существующих файлов `.wa`.
- 🎨 **Смена тем и цвета редактора**: Переключение готовых палитр и тем оформления интерфейса (*Вид -> Тема оформления*) с автоматическим сохранением выбранного цвета и стиля между перезапусками.
- ⚡ **Мульти-выделение окон (`Ctrl + Клик`)**: Выделение сразу нескольких окон на холсте и панелях с массовым редактированием заголовков, текстов, иконок и звуков.
- ↺ **История изменений и Undo (`Ctrl + Z`)**: Полноценный 50-шаговый стек отмены любых действий, включая перемещения окон и изменения настроек кадров.
- 🗑️ **Горячие клавиши удаления (`Backspace`)**: Быстрое удаление одного или группы выделенных окон нажатием одной клавиши.
- 📁 **Автоматическая папка проектов**: Проекты по умолчанию сохраняются и открываются в каталоге `Documents/windownimator_projects`.
- 📦 **Полноценный установщик Windows**: Инсталлятор `Windownimator_v2.1.0_Setup.exe` с выгрузкой в Program Files и ярлыками.
- ℹ️ **Окно «О программе»**: Быстрый доступ к информации о релизе и прямой ссылке на открытый репозиторий GitHub.

## Быстрый запуск (.exe)

Скачайте инсталлятор **`Windownimator_v2.1.0_Setup.exe`** или портативную верcию **`Windownimator_v2.1.0.exe`** со страницы [Releases](https://github.com/arsenjkin459g-source/windownimator/releases).

### Сборка из исходного кода

```bash
git clone https://github.com/arsenjkin459g-source/windownimator.git
cd windownimator
pip install PySide6 pygame-ce pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Windownimator_v2.0.0" --icon "windownimator.ico" --add-data "assets;assets" main.py
```
