# BATCH_078 — Media Production: Publishing, Journalism, Photography, Video Workflows
# world_skills_core · source: world_skills_core:batch_078:media_production
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| mediaprod.journalism.role | Роль журналистики | invariant | информирование общества, контроль власти (четвёртая власть) | основа осведомлённого общества |
| mediaprod.journalism.5w | Принцип 5W+H | invariant | who, what, when, where, why, how — каркас новости | полнота сообщения |
| mediaprod.journalism.inverted_pyramid | Перевёрнутая пирамида | invariant | главное в начале, детали ниже | структура новостного текста |
| mediaprod.journalism.sources | Работа с источниками | invariant | проверка, минимум два независимых, защита анонимных | достоверность |
| mediaprod.journalism.factcheck | Фактчекинг | invariant | проверка утверждений перед публикацией | борьба с дезинформацией |
| mediaprod.journalism.ethics | Журналистская этика | invariant | правдивость, баланс, разделение факта и мнения, минимизация вреда | доверие к СМИ |
| mediaprod.journalism.objectivity | Объективность и предвзятость | variant | стремление к беспристрастности; осознание уклона | качество подачи |
| mediaprod.journalism.libel | Клевета и диффамация | invariant | ложные порочащие утверждения — юридическая ответственность | правовые границы |
| mediaprod.publishing.process | Издательский процесс | invariant | рукопись → редактура → вёрстка → корректура → печать/публикация | путь книги к читателю |
| mediaprod.publishing.editing_levels | Уровни редактуры | variant | структурная → литературная → корректура | качество текста |
| mediaprod.publishing.isbn | ISBN | invariant | уникальный идентификатор издания | учёт и торговля книгами |
| mediaprod.publishing.copyright | Авторское право | invariant | защита произведения с момента создания | права автора и издателя |
| mediaprod.publishing.layout | Вёрстка и типографика | variant | шрифты, кегль, интерлиньяж, поля, сетка | читаемость и вид |
| mediaprod.publishing.formats | Форматы публикации | variant | печать, ePub, PDF, аудиокнига | каналы дистрибуции |
| mediaprod.photo.exposure | Экспозиция | invariant | количество света на матрицу — диафрагма, выдержка, ISO | базовый контроль кадра |
| mediaprod.photo.triangle | Экспотреугольник | invariant | диафрагма (глубина) × выдержка (движение) × ISO (шум) | компромисс параметров |
| mediaprod.photo.aperture | Диафрагма (f/число) | invariant | размер отверстия; меньше f → больше света и меньше ГРИП | глубина резкости |
| mediaprod.photo.shutter | Выдержка | invariant | время экспонирования; короткая замораживает движение | резкость движения |
| mediaprod.photo.iso | ISO (светочувствительность) | invariant | выше ISO → ярче, но больше шума | съёмка при низком свете |
| mediaprod.photo.composition | Композиция кадра | variant | правило третей, направляющие линии, кадрирование | выразительность |
| mediaprod.photo.lighting | Свет в фотографии | invariant | жёсткий/мягкий, направление, золотой час | настроение и объём |
| mediaprod.photo.whitebalance | Баланс белого | invariant | коррекция цветовой температуры под источник | естественные цвета |
| mediaprod.photo.raw | RAW vs JPEG | variant | RAW — максимум данных для обработки; JPEG — готовый | гибкость постобработки |
| mediaprod.photo.lens | Объективы и фокусное | variant | широкоугольный, нормальный, теле, макро | выбор под сюжет |
| mediaprod.video.framerate | Частота кадров (fps) | invariant | 24 (кино), 30, 60+; влияет на плавность | стиль и восприятие |
| mediaprod.video.resolution | Разрешение | variant | HD, 4K, 8K — детализация изображения | качество и объём файла |
| mediaprod.video.codec | Кодек и контейнер | invariant | сжатие (H.264/H.265) внутри контейнера (MP4, MOV) | размер vs качество |
| mediaprod.video.bitrate | Битрейт | variant | объём данных в секунду — качество против размера | стриминг и хранение |
| mediaprod.video.shot_types | Планы съёмки | variant | общий, средний, крупный, деталь | язык монтажа |
| mediaprod.video.180_rule | Правило 180 градусов | invariant | камера по одну сторону оси действия | сохранение ориентации зрителя |
| mediaprod.video.editing | Монтаж | invariant | отбор, склейка, ритм, переходы | смысл и темп истории |
| mediaprod.video.continuity | Непрерывность (continuity) | variant | согласованность деталей между дублями | целостность сцены |
| mediaprod.video.color_grading | Цветокоррекция | variant | техническая коррекция + творческий грейдинг | вид и атмосфера |
| mediaprod.audio.recording | Запись звука | invariant | микрофоны, уровни, защита от перегруза | разборчивость и качество |
| mediaprod.audio.types_mic | Типы микрофонов | variant | динамический, конденсаторный, петличный, пушка | выбор под задачу |
| mediaprod.audio.mixing | Сведение звука | variant | баланс диалогов, музыки, эффектов | комфортное восприятие |
| mediaprod.audio.loudness | Громкость (LUFS) | variant | нормализация громкости для вещания/стриминга | единый уровень |
| mediaprod.workflow.preproduction | Препродакшн | invariant | сценарий, раскадровка, планирование, локации | основа успешной съёмки |
| mediaprod.workflow.production | Продакшн (съёмка) | invariant | реализация плана на площадке | сбор материала |
| mediaprod.workflow.postproduction | Постпродакшн | invariant | монтаж, звук, цвет, графика, экспорт | финальный продукт |
| mediaprod.storage.backup | Резервирование медиа | invariant | большие файлы; 3-2-1 против потери отснятого | страховка контента |
| mediaprod.digital.streaming | Стриминг и доставка | variant | адаптивный битрейт, CDN, платформы | распространение видео |
| mediaprod.rights.licensing | Лицензирование контента | variant | музыка, стоки, релизы моделей | юридическая чистота |
| mediaprod.ethics.manipulation | Этика обработки | invariant | граница между улучшением и искажением (особенно в новостях) | доверие к изображению |
