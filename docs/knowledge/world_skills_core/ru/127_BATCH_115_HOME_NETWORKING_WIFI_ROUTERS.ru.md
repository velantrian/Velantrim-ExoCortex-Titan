# BATCH_115 — Home Networking: Wi-Fi, Routers, Troubleshooting
# world_skills_core · source: world_skills_core:batch_115:home_networking
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| homenet.basic.lan_wan | ЛВС и ГВС | invariant | локальная сеть дома vs внешняя (интернет) | структура подключения |
| homenet.basic.isp | Интернет-провайдер | invariant | даёт доступ в интернет через WAN | подключение |
| homenet.device.router | Маршрутизатор (роутер) | invariant | соединяет домашнюю сеть с интернетом, раздаёт Wi-Fi | сердце домашней сети |
| homenet.device.modem | Модем | variant | преобразует сигнал провайдера; часто в роутере | подключение к ISP |
| homenet.device.switch | Коммутатор (свитч) | variant | расширяет число проводных портов | больше устройств |
| homenet.device.access_point | Точка доступа | variant | добавляет/расширяет Wi-Fi | покрытие |
| homenet.ip.address | IP-адрес | invariant | уникальный адрес устройства в сети | адресация |
| homenet.ip.private | Частные IP | invariant | 192.168.x.x, 10.x.x.x — внутри дома | локальная сеть |
| homenet.ip.public | Публичный IP | invariant | внешний адрес от провайдера | виден из интернета |
| homenet.ip.dhcp | DHCP | invariant | роутер автоматически раздаёт IP устройствам | без ручной настройки |
| homenet.ip.static | Статический IP | variant | фиксированный адрес устройству | серверы, принтеры |
| homenet.ip.nat | НАТ | invariant | много устройств через один публичный IP | основа домашней сети |
| homenet.ip.ipv4_ipv6 | IPv4 и IPv6 | invariant | старое (исчерпано) и новое адресное пространство | переход на IPv6 |
| homenet.dns.role | DNS | invariant | переводит имена сайтов в IP | навигация в интернете |
| homenet.dns.change | Смена DNS | variant | публичные DNS (8.8.8.8, 1.1.1.1) — скорость/фильтрация | настройка |
| homenet.wifi.bands | Диапазоны 2.4 и 5 ГГц | invariant | 2.4 — дальше/медленнее, 5 — быстрее/ближе | выбор сети |
| homenet.wifi.standards | Стандарты Wi-Fi | variant | 802.11 n/ac/ax (Wi-Fi 4/5/6) | скорость |
| homenet.wifi.channels | Каналы Wi-Fi | variant | пересечение каналов = помехи | выбор свободного канала |
| homenet.wifi.ssid | SSID (имя сети) | invariant | название Wi-Fi-сети | идентификация |
| homenet.wifi.signal | Сила и качество сигнала | invariant | падает с расстоянием и стенами | размещение роутера |
| homenet.wifi.placement | Размещение роутера | variant | центр, выше, вдали от помех (СВЧ, металл) | покрытие |
| homenet.wifi.mesh | Mesh-система | variant | несколько узлов = бесшовное покрытие | большие дома |
| homenet.wifi.extender | Репитер/усилитель | variant | расширяет зону, но снижает скорость | дальние комнаты |
| homenet.sec.password | Пароль Wi-Fi | invariant | надёжный пароль защищает сеть | безопасность |
| homenet.sec.wpa | Шифрование WPA2/WPA3 | invariant | защищает трафик; не использовать WEP/открытую | безопасность |
| homenet.sec.guest | Гостевая сеть | variant | изолирует гостей от домашних устройств | защита |
| homenet.sec.admin | Смена пароля админа роутера | invariant | дефолтные пароли опасны | защита от взлома |
| homenet.sec.firmware | Обновление прошивки роутера | invariant | закрывает уязвимости | безопасность |
| homenet.sec.firewall | Файрвол роутера | variant | блокирует нежелательные подключения | защита сети |
| homenet.connect.ethernet | Проводное (Ethernet) | invariant | стабильнее и быстрее Wi-Fi | игры, ТВ, ПК |
| homenet.connect.cable_cat | Категории кабеля (Cat5e/6) | variant | поддерживаемая скорость | проводка |
| homenet.connect.powerline | Powerline-адаптеры | variant | сеть через электропроводку | без прокладки кабеля |
| homenet.iot.devices | Умный дом (IoT) | variant | много устройств в сети; изолировать | безопасность, нагрузка |
| homenet.qos.priority | QoS / приоритизация | variant | приоритет видео/играм над фоном | стабильность |
| homenet.tool.speedtest | Тест скорости | invariant | измеряет реальную скорость | диагностика |
| homenet.tool.ping | Ping и задержка | invariant | время отклика; высокий пинг → лаги | диагностика |
| homenet.trouble.no_internet | Нет интернета | invariant | алгоритм: устройство → Wi-Fi → роутер → провайдер | поиск причины |
| homenet.trouble.reboot | Перезагрузка роутера | invariant | решает большинство временных сбоев | первый шаг |
| homenet.trouble.slow | Медленный интернет | variant | помехи, перегрузка канала, расстояние, тариф | диагностика |
| homenet.trouble.dropouts | Обрывы соединения | variant | помехи, перегрев, старая прошивка | устранение |
| homenet.trouble.ip_conflict | Конфликт IP-адресов | variant | два устройства с одним IP | DHCP решает |
| homenet.vpn.basics | VPN | variant | шифрует трафик, меняет видимый IP | приватность, доступ |
| homenet.bandwidth.usage | Потребление трафика | variant | видео/игры/загрузки делят канал | управление нагрузкой |
| homenet.wifi.health | Wi-Fi и здоровье | invariant | мощность бытового Wi-Fi безопасна по нормам | факт против мифов |
