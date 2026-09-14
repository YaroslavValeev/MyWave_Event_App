# MyWave Event App — сценарий режиссера трансляции

**Дата:** 14.09.2026  
**Статус:** целевая спецификация для реализации и проверки  
**Роль:** режиссер трансляции / broadcast director

## 1. Назначение

Режиссер объединяет verified live data, камеры, графику, повторы, ведущего, рекламу и аварийный план. Event App дает ему достоверный контекст, но не заменяет режиссерский пульт и не является системой видеомикширования.

## 2. Команда режиссуры

| Роль | Задача |
|---|---|
| Broadcast director | Принимает решения по эфиру и темпу |
| Producer | Отвечает за rundown, контент и timing |
| Technical director | Отвечает за feed, devices, network и recovery |
| Graphics operator | Выводит lower thirds и результаты |
| Replay operator | Готовит повторы проездов |
| Camera director/lead | Управляет камерами и shot list |
| Audio director | Микрофоны ведущего, ambient, safety ducking |
| Stream operator | Encoder, platform health, recording |
| Commentator/host | Ведет эфир и озвучивает verified facts |
| Media manager | Approved photo/video и права |

## 3. Источники данных

Режиссер получает:

- current/next heat;
- verified start list;
- official results;
- public athlete profile;
- approved media;
- delay/hold status;
- sponsor cues;
- emergency wording.

Не получает:

- judge drafts;
- медицинские и финансовые сведения;
- private contacts;
- restricted media;
- неподтвержденные достижения.

У каждого блока виден статус `official / verified / draft / changed / restricted`.

## 4. Тайминг

### D‑45…D‑30

- определить платформу и формат эфира;
- зафиксировать camera plan;
- определить graphic templates;
- настроить Event App feed;
- согласовать sponsor package;
- определить права на media;
- создать rundown и fallback.

### D‑21…D‑7

- связать heat с lower third;
- проверить Athlete ID и публичные имена;
- загрузить approved portraits/clips;
- протестировать result publish;
- настроить replay naming;
- проверить delay и hold cues;
- провести technical rehearsal.

### D‑1

- зафиксировать release/version;
- проверить источники времени;
- проверить резервный stream;
- проверить offline/printed rundown;
- проверить emergency slate;
- подтвердить контакт TD и event director.

## 5. Broadcast dashboard

### Current

- блок;
- раунд;
- heat;
- участник;
- стартовый номер;
- category;
- actual time;
- live status;
- verified result;
- media cue;
- camera cue.

### Next

- следующие участники;
- новый порядок;
- ETA;
- изменения;
- подготовленные титры.

### Technical

- stream health;
- encoder;
- audio;
- graphics feed;
- replay queue;
- network;
- storage;
- last sync.

### Editorial

- presenter cue;
- sponsor block;
- interview;
- replay;
- hold wording;
- return-to-live.

## 6. Передача события в эфир

Режиссер работает по цепочке:

`rundown → cue → camera/graphic → presenter → official result → replay/media → archive log`.

Для каждого cue видны:

- тип;
- время;
- владелец;
- статус;
- asset;
- rights;
- текст;
- возможность пропустить или перенести.

### Lower third

Перед выводом проверяются:

- публичное имя;
- Athlete ID, если он входит в графику;
- стартовый номер;
- категория;
- round/heat;
- verified status.

### Result graphic

Результат выводится только после `official/published`. Draft score никогда не попадает в эфирную графику.

### Replay

Replay получает:

- event ID;
- round;
- heat;
- Athlete ID;
- timecode;
- public scope;
- approved status.

## 7. Работа с задержками и изменениями

При hold/delay режиссер:

1. останавливает устаревший cue;
2. открывает новую версию расписания;
3. проверяет affected heats;
4. выбирает approved wording;
5. меняет rundown;
6. отмечает новое время;
7. уведомляет ведущего и команду.

В эфире не объясняется непроверенная причина. Если причина safety/medical, используется нейтральная формулировка.

## 8. Инцидентный эфирный режим

### Потеря live data

- перейти на последнюю verified snapshot;
- явно пометить ее временем;
- не объявлять новые results;
- запросить восстановление у TD;
- включить резервный editorial block.

### Ошибка графики

- снять graphic;
- сохранить screenshot/log;
- отметить flag;
- вернуть neutral template;
- запросить исправленную версию.

### Потеря трансляции

- переключить backup encoder/канал;
- вывести holding slate;
- сохранить локальную запись;
- отметить outage time;
- уведомить event director.

### Medical/safety incident

- убрать неподходящие camera shots;
- включить approved wording;
- не показывать травмирующие подробности;
- передать эфир ведущему/продюсеру по кризисному плану.

## 9. Спонсорские интеграции

Режиссер видит только утвержденные:

- логотип;
- текст;
- длительность;
- позицию в rundown;
- visual;
- обязательную атрибуцию;
- статус выполнено.

Редакционная информация и реклама визуально различаются. Нельзя менять sponsor wording в live без approval.

## 10. Ведущий и режиссер

Режиссер передает ведущему:

- текущий heat;
- следующего спортсмена;
- verified context;
- result status;
- delay wording;
- interview cue;
- sponsor cue.

Ведущий передает режиссеру:

- готовность к переходу;
- запрос replay;
- необходимость уточнения имени;
- сигнал, что информация конфликтует.

Не допускается передавать в эфирный talkback медицинские и приватные сведения.

## 11. AI Agents

| Agent | Разрешенная работа | Запрещено |
|---|---|---|
| Rundown Agent | Следит за временем и предлагает перестановки | Самостоятельно менять эфир |
| Data Feed Agent | Показывает current/next и изменения | Выдавать draft как official |
| Graphics Agent | Готовит verified lower thirds | Публиковать без operator approval |
| Replay Agent | Находит clip по heat/timecode | Выводить unapproved media |
| Delay Agent | Предлагает neutral wording | Раскрывать непроверенную причину |
| Sponsor Agent | Напоминает о согласованной интеграции | Менять коммерческий текст |
| Incident Agent | Сводит outage и owner | Закрывать SEV‑0/1 |
| Archive Agent | Сохраняет cue и использованные assets | Публиковать transcript без review |

AI показывает источник и актуальность каждого существенного факта. Финальное решение остается у режиссера, продюсера и ответственной роли.

## 12. После эфира

Режиссер закрывает:

- эфирный log;
- использованные media assets;
- sponsor delivery;
- replay links;
- technical incidents;
- corrections;
- final recording;
- связь cue с Event ID и round.

После завершения события доступ к live control отзывается, а материалы передаются в read-only archive.

## 13. Definition of Done

- режиссер входит только в назначенное событие;
- current/next heat всегда имеют версию;
- draft result не попадает в эфир;
- lower third строится из verified данных;
- replay связан с heat/timecode/Athlete ID;
- approved media проверяется по consent;
- задержка создает новую версию rundown;
- есть backup stream и holding slate;
- network outage не приводит к выдуманным объявлениям;
- sponsor cues имеют approval;
- приватные данные недоступны;
- incident log сохраняется;
- использованные assets входят в архив;
- техническая репетиция проходит до live.

## 14. Первый технический slice

`создать test event → загрузить 1 heat → открыть broadcast dashboard → вывести lower third → провести test run → опубликовать official result → вызвать replay → применить delay → переключить holding slate → восстановить feed → записать cue log → закрыть event`.

Главный критерий: трансляция получает своевременные и проверенные данные, а режиссер может продолжить эфир при задержке, потере связи или временной недоступности scoring.
