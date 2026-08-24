# Accessibility (a11y)

**Дата:** 2026-08-04  

## 1. Цель Stage 1–2

WCAG 2.2 AA pragmatic baseline для Web UI.

## 2. Обязательные практики

- Семантические landmarks: `header`, `main`, `nav`.
- Клавиатурная навигация всех интерактивных элементов.
- Видимый `focus-visible`.
- Контраст текста достаточный (не полагаться только на цвет статуса).
- Формы: `label` + `aria-invalid` + текст ошибки.
- Модалки: focus trap, Escape, `role="dialog"`, `aria-modal`.
- Live regions для статуса сохранения результата (`aria-live="polite"`).

## 3. Роли и экраны приоритета

1. Публичная витрина результатов.
2. Форма заявки участника.
3. Судейский ввод результата.
4. Админ: назначение ролей.

## 4. Проверки

- Ручной keyboard pass перед релизом UI.
- axe DevTools / eslint-plugin-jsx-a11y — по мере подключения.
- Не блокировать релиз только «идеальным 100 score», но P0-дефекты a11y чинить до merge.

## 5. Вне скоупа Stage 1

- Полный screen-reader certification.
- Нативные mobile a11y guidelines (нет мобильных сборок).
