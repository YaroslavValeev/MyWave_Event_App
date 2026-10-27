"""Public metadata for MyWave Event App release artifacts.

Target URLs live only in environment variables. Placeholders in this catalog
are documentation for operators, never served as download links.
"""

from __future__ import annotations

from typing import Any

ARTIFACT_IDS = ("android", "ios", "source", "documentation")

APP_DOWNLOADS_CATALOG: dict[str, Any] = {
    "app": {
        "id": "mywave-event-app",
        "name": "MyWave Event App",
        "short_description": (
            "Цифровая платформа соревнований MyWave: заявка, старт, судейство "
            "и протокол в одном веб-приложении для телефона и компьютера."
        ),
        "features": [
            "Программа соревнования, стартовые списки и статусы заездов",
            "Роли участника, судьи, главного судьи и организатора",
            "Документы события, чек-лист подготовки и уведомления",
            "Результаты и протокол по правилам публикации",
            "Веб-приложение (PWA) в браузере телефона — нативные сборки подключаются отдельно",
        ],
        "version": "0.5.10",
        "last_updated": "2026-09-16",
        "platforms": [
            "Веб-приложение (PWA)",
            "Android",
            "iOS / TestFlight",
            "Исходный код",
            "Документация",
        ],
    },
    "artifacts": [
        {
            "id": "android",
            "label": "Android",
            "platform": "Android",
            "format": "APK / AAB",
            "target_env": "MYWAVE_EVENT_APP_ANDROID_DOWNLOAD_URL",
            "placeholder": "{{android_download_url}}",
            "version": "Не опубликована",
            "size": None,
            "last_updated": "2026-09-16",
            "action_label": "Скачать сборку для Android",
            "open_in_new_tab": False,
            "requirements": [
                "Android 9 или новее",
                "Не менее 250 МБ свободного места",
                "Разрешение установки из доверенного источника для APK",
            ],
        },
        {
            "id": "ios",
            "label": "iOS / TestFlight",
            "platform": "iOS",
            "format": "TestFlight",
            "target_env": "MYWAVE_EVENT_APP_IOS_TESTFLIGHT_URL",
            "placeholder": "{{ios_testflight_url}}",
            "version": "Не опубликована",
            "size": None,
            "last_updated": "2026-09-16",
            "action_label": "Открыть TestFlight",
            "open_in_new_tab": True,
            "requirements": [
                "iOS 16 или новее",
                "Установленное приложение TestFlight",
                "Apple ID с доступом к тестированию",
            ],
        },
        {
            "id": "source",
            "label": "Исходный код",
            "platform": "Разработка",
            "format": "ZIP",
            "target_env": "MYWAVE_EVENT_APP_SOURCE_ARCHIVE_URL",
            "placeholder": "{{source_archive_url}}",
            "version": "Не опубликована",
            "size": None,
            "last_updated": "2026-09-16",
            "action_label": "Скачать исходный код",
            "open_in_new_tab": False,
            "requirements": [
                "Git 2.40 или новее",
                "Python 3.11+, Node.js 20+ согласно README архива",
                "Переменные окружения проекта из .env.example",
            ],
        },
        {
            "id": "documentation",
            "label": "Документация",
            "platform": "Все платформы",
            "format": "PDF / HTML / ZIP",
            "target_env": "MYWAVE_EVENT_APP_DOCUMENTATION_URL",
            "placeholder": "{{documentation_url}}",
            "version": "0.5.10",
            "size": None,
            "last_updated": "2026-09-16",
            "action_label": "Скачать документацию",
            "open_in_new_tab": True,
            "requirements": [
                "Современный браузер или программа для PDF",
                "Доступ к инструкции по установке и запуску",
            ],
        },
    ],
}
