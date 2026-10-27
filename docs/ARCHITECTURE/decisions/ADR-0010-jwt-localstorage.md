# ADR-0010 — JWT в localStorage (Stage 1)

**Дата:** 2026-09-16  
**Статус:** accepted (временный риск до native / cookie-сессии)  
**Связанный долг:** TD-02

## Контекст

Stage 1 веб-клиент хранит Bearer JWT в `localStorage` и передаёт его заголовком `Authorization`. Это удобно для PWA и текущего App Router без server-session. Угроза XSS → кража токена известна (THREAT_MODEL, TD-02).

До native-оболочек и до публичного production cookie vs JWT не был явно принят — долг «до первого staging» уже просрочен: staging работает.

## Решение

1. **Сейчас (PWA 0.5.10):** оставляем Bearer JWT в `localStorage`. Не мигрируем молча на httpOnly cookie в этом цикле — это ломает текущий клиент и требует CSRF-модели.
2. **Риск принимаем явно:** XSS на домене приложения = сессия атакующего. Смягчения: короткий TTL, `token_expired` → «Войти снова» с `?next=`, гостевые публичные маршруты без 401, без секретов в git.
3. **До native Android/iOS:** не класть тот же JWT в незащищённый WebView storage без Secure Storage / httpOnly cookie на API-домене.
4. **Следующий шаг (не этот цикл):** отдельный ADR на cookie-сессию (`Set-Cookie` httpOnly, SameSite) или Capacitor Secure Storage. Смена — отдельный PR, не часть UX Role Based.

## Последствия

- Staging и отладка PWA продолжаются без переписывания auth.
- Pen-test / публичный prod не закрывать, пока TD-02 открыт.
- Агентам запрещено «тихо» переехать на cookie в том же PR, что UX.
