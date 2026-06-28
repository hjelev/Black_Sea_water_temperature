// Lightweight i18n layer for the static Black Sea Temperature site.
// Loaded in <head> before data.js / inline scripts so t() is available everywhere.

const I18N = {
    en: {
        // <title> tags
        title_dashboard: 'Black Sea Water Temperature',
        title_compare:   'Compare Years — Black Sea Water Temperature',
        title_heatmap:   'Monthly Heatmap — Black Sea Water Temperature',
        title_stats:     'Statistics — Black Sea Water Temperature',
        title_comparelocations: 'Compare Locations — Black Sea Water Temperature',

        // Nav (shared)
        nav_brand:     '🌊 Black Sea Temp',
        nav_dashboard: 'Dashboard',
        nav_compare:   'Compare Years',
        nav_heatmap:   'Heatmap',
        nav_stats:     'Statistics',
        nav_comparelocations: 'Compare Locations',
        nav_location:  'Location',
        nav_menu:      'Menu',

        // Footer (shared)
        footer_title: 'Black Sea Water Temperature',

        // Locations (shared)
        loc_burgas:      'Burgas, Bulgaria',
        loc_sinemorets:  'Sinemorets, Bulgaria',
        loc_varna:       'Varna, Bulgaria',
        loc_kamenbryag:  'Kamen Bryag, Bulgaria',
        loc_tyulenovo:   'Tyulenovo, Bulgaria',
        loc_nessebar:    'Nessebar, Bulgaria',
        loc_sozopol:     'Sozopol, Bulgaria',
        loc_sunnybeach:  'Sunny Beach, Bulgaria',
        loc_goldensands: 'Golden Sands, Bulgaria',
        loc_balchik:     'Balchik, Bulgaria',
        loc_capekaliakra: 'Cape Kaliakra, Bulgaria',
        loc_albena:      'Albena, Bulgaria',
        loc_svetikonstantin: 'St. Konstantin and Elena, Bulgaria',
        loc_irakli:      'Irakli Beach, Bulgaria',
        loc_pomorie:     'Pomorie, Bulgaria',
        loc_primorsko:   'Primorsko, Bulgaria',
        loc_lozenets:    'Lozenets, Bulgaria',
        loc_svetivlas:   'Sveti Vlas, Bulgaria',

        // index.html (hub)
        hub_h1:       'Black Sea Water Temperature',
        hub_subtitle: "Live and historical sea surface temperature for Bulgaria's Black Sea coast",
        hub_map:      'Current water temperature',
        hub_pick:     'Choose a location',
        map_view:     'View dashboard',

        // index.html
        dash_h1:          'Dashboard',
        dash_subtitle:    'Black Sea water temperature — {location}',
        dash_stats_loading: 'Temperature on this date (loading…)',
        dash_stats_title: 'Temperature on {date} — last 5 years',
        dash_last30:      'Last 30 Days',
        dash_full:        'Full History',
        dash_full_tip:    'Zoom or select a range below to explore historical data.',

        // Location descriptions (dashboard)
        desc_burgas: "The largest city on Bulgaria's southern Black Sea coast, Burgas is a vibrant port and cultural hub set between the sea and a string of tranquil coastal lakes rich in birdlife. Its elegant Sea Garden park stretches along the shore, leading to a long central beach and a lively pedestrian center full of cafés and galleries. The city serves as the main gateway to the southern resorts while offering its own relaxed, cosmopolitan seaside atmosphere.",
        desc_sinemorets: "Located deep in the south within the protected Strandzha Nature Park, this village is rich in biodiversity and offers a rugged, unspoiled landscape. It is home to some of the most beautiful and unique beaches in the country, where the Veleka River meets the sea to create stunning sandbars. Its history is deeply rooted in the local traditions of the Strandzha region, making it an excellent destination for those wanting to explore raw nature and tranquility.",
        desc_varna: "Known as the \"sea capital\" of Bulgaria, this major city is the heir to an ancient Thracian settlement and later a Roman spa town. It boasts iconic landmarks like the Roman Thermae and the extensive Sea Garden, which stretches along the city's vast, golden-sand beaches. The city provides a cosmopolitan urban environment alongside easy access to the pristine seaside.",
        desc_kamenbryag: "This remote northern village sits atop rugged coastal cliffs and is famous for the nearby Yailata archaeological reserve, with its ancient cave dwellings and rock tombs carved into the stone. Rather than wide sandy beaches, the coastline here offers dramatic rocky shelves, hidden coves, and crystal-clear water favored by divers and free spirits. It is best known for hosting the July Morning celebration, when crowds gather on the cliffs to greet the first sunrise of the month.",
        desc_tyulenovo: "Named after the monk seals that once inhabited its shores, this tiny fishing village is celebrated for its spectacular sea caves, natural rock arches, and sheer cliffs plunging into deep, transparent water. There is no traditional beach, but the dramatic rocky coastline has made it a magnet for cliff divers, climbers, and underwater explorers. Its quiet, end-of-the-world charm offers an unspoiled escape far from the crowded resorts to the south.",
        desc_nessebar: "This UNESCO World Heritage site is a historic treasure featuring an ancient Old Town on a peninsula with Byzantine-era churches and cobblestone streets. Visitors can explore its rich history before heading to the modern, sandy beaches that stretch along the coastline of the new town. It perfectly balances the charm of antiquity with the amenities of a contemporary seaside resort.",
        desc_sozopol: "As one of Bulgaria's oldest towns, Sozopol is famous for its romantic Old Town filled with traditional 19th-century wooden houses and narrow, winding alleys. The town is flanked by beautiful, scenic beaches like Harmanite and the nearby camping areas, making it a favorite for those who enjoy a blend of cultural exploration and sunbathing. Its relaxed atmosphere and ancient ruins provide a unique coastal experience.",
        desc_sunnybeach: "Bulgaria's largest and most famous resort destination, it was developed as a modern vacation hub and now draws thousands for its high-energy nightlife and entertainment. The resort is renowned for its wide, sweeping stretch of fine, sun-drenched sand that runs for kilometers along the coast. It is the premier spot for those seeking non-stop action, water sports, and vibrant beach bars.",
        desc_goldensands: "This popular northern resort is steeped in legend, with myths claiming that pirates buried golden treasure here that turned into the resort's signature fine, golden sand. It is surrounded by a lush National Park that slopes down to meet the sparkling sea, offering a perfect mix of nature and luxury tourism. The beach itself is expansive and well-managed, attracting visitors with its mineral springs and extensive resort amenities.",
        desc_balchik: "Historically significant for its stunning palace, which served as the summer residence of Queen Marie of Romania, the town is a blend of Mediterranean and Balkan architectural styles. It is particularly famous for its exotic botanical gardens that cascade down the cliffs toward the water. The local beaches are smaller and more intimate, providing a quiet alternative to the larger, busier resorts.",
        desc_capekaliakra: "This dramatic, narrow headland is a significant archaeological site home to the ruins of an ancient medieval fortress and a legend-rich history. While the area is defined by its towering 70-meter cliffs and panoramic sea views rather than a traditional beach, it offers small, hidden coves at the base of the rocks. It is a premier destination for those interested in nature, bird migration, and ancient history.",
        desc_albena: "Designed specifically for tourism, this resort is celebrated for its organized, family-friendly environment and its lush parkland setting. It features a broad, Blue Flag-certified beach known for its clean, shallow waters and fine sand, making it exceptionally safe for children. The entire complex is surrounded by greenery, offering a peaceful and well-maintained atmosphere for a classic seaside holiday.",
        desc_svetikonstantin: "As the oldest resort on the Bulgarian coast, it carries a legacy of wellness and is renowned for its healing mineral springs and thermal pools. The coastline here is characteristically rocky and intimate, featuring several small, quiet, and charming boutique beaches hidden among the trees. It is an ideal destination for those looking for a relaxing, spa-oriented getaway away from the crowds.",
        desc_irakli: "A sanctuary for nature lovers, this is one of the few remaining wild, undeveloped beaches on the coast, known for its pristine beauty and lack of commercial infrastructure. Its history is tied to the untouched landscape near the village of Emona, where the Balkan Mountains meet the sea at Cape Emine. It remains a favorite destination for campers and those seeking a tranquil, natural escape.",
        desc_pomorie: "This ancient town is situated on a narrow, rocky peninsula and is famous for its salt pans and therapeutic mineral-rich mud treatments. Its history dates back to antiquity, with local landmarks like the Thracian \"Bee-Hive Tomb\" showcasing the region's deep cultural roots. The beaches here are unique, often featuring dark, mineral-rich sand and calm waters perfect for health-focused tourism.",
        desc_primorsko: "Originally a small fishing settlement, this town has grown into a vibrant youth-oriented resort with a relaxed, small-town charm. It is located on a cape that provides two distinct, sprawling, and clean sandy beaches—one to the north and one to the south. It is widely favored for its affordable accommodation, lively nightlife, and beautiful natural dunes.",
        desc_lozenets: "Once a sleepy fishing village, Lozenets has transformed into a stylish, trendy destination known for its relaxed \"bohemian\" vibe. The area features several beautiful, golden-sand beaches that are popular among both young families and the younger social crowd. It remains a preferred spot for those who want a blend of modern beach bars and a laid-back, coastal atmosphere.",
        desc_svetivlas: "This town is historically significant as a quiet settlement that has developed into a premier luxury yachting destination with a massive, modern marina. It sits at the foot of the Balkan Mountains, offering a beautiful contrast between the green slopes and the deep blue sea. Its beaches are well-kept and offer a slightly more upscale, peaceful experience compared to its bustling neighbor, Sunny Beach.",

        // compare.html
        cmp_h1:        'Compare Years',
        cmp_subtitle:  'Overlay selected years on a Jan–Dec axis to spot seasonal patterns',
        cmp_from:      'From',
        cmp_to:        'To',
        cmp_smooth:    'Smooth (7-day avg)',
        cmp_timeline:  'Timeline selector',
        cmp_tip:       'Drag to select a date range — updates the year checkboxes above.',

        // compare-locations.html
        cl_h1:           'Compare Locations',
        cl_subtitle:     'Overlay water temperature for different towns along the Black Sea coast',
        cl_smooth:       'Smooth (7-day avg)',
        cl_timeline_h2:  'Across the years',
        cl_timeline_tip: 'Each line is a location over the full record. Toggle towns above.',
        cl_seasonal_h2:  'Seasonal (single year)',
        cl_seasonal_tip: 'Selected year only, mapped onto a Jan–Dec axis to compare seasons.',
        cl_year:         'Year',

        // heatmap.html
        hm_h1:         'Monthly Heatmap',
        hm_subtitle:   'Average water temperature per month across all years ({year}–present)',
        hm_monthly:    'Monthly Averages by Year',
        hm_tip:        'Each cell shows the mean temperature for that month/year. Hover for exact values.',

        // stats.html
        st_h1:          'Statistics &amp; Records',
        st_subtitle:    'All-time records and annual statistics since {year}',
        st_records:     'All-time Records',
        st_annual:      'Annual Min / Avg / Max',
        st_trend:       'Long-term Trend',
        st_trend_tip:   'Yearly average with a 5-year moving average trend line.',
        st_hottest:     'Hottest reading',
        st_coldest:     'Coldest reading',
        st_warmest_yr:  'Warmest year (avg)',
        st_coldest_yr:  'Coldest year (avg)',
        st_max:         'Max',
        st_avg:         'Avg',
        st_min:         'Min',
        st_yearly_avg:  'Yearly avg',
        st_trend_5yr:   '5-yr trend',

        months: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    },

    bg: {
        // <title> tags
        title_dashboard: 'Температура на водата в Черно море',
        title_compare:   'Сравнение по години — Температура на Черно море',
        title_heatmap:   'Месечна карта — Температура на Черно море',
        title_stats:     'Статистика — Температура на Черно море',
        title_comparelocations: 'Сравнение на локации — Температура на Черно море',

        // Nav (shared)
        nav_brand:     '🌊 Черно море',
        nav_dashboard: 'Табло',
        nav_compare:   'Сравнение по години',
        nav_heatmap:   'Топлинна карта',
        nav_stats:     'Статистика',
        nav_comparelocations: 'Сравнение на локации',
        nav_location:  'Локация',
        nav_menu:      'Меню',

        // Footer (shared)
        footer_title: 'Температура на водата в Черно море',

        // Locations (shared)
        loc_burgas:      'Бургас, България',
        loc_sinemorets:  'Синеморец, България',
        loc_varna:       'Варна, България',
        loc_kamenbryag:  'Камен бряг, България',
        loc_tyulenovo:   'Тюленово, България',
        loc_nessebar:    'Несебър, България',
        loc_sozopol:     'Созопол, България',
        loc_sunnybeach:  'Слънчев бряг, България',
        loc_goldensands: 'Златни пясъци, България',
        loc_balchik:     'Балчик, България',
        loc_capekaliakra: 'Нос Калиакра, България',
        loc_albena:      'Албена, България',
        loc_svetikonstantin: 'Св. св. Константин и Елена, България',
        loc_irakli:      'Иракли, България',
        loc_pomorie:     'Поморие, България',
        loc_primorsko:   'Приморско, България',
        loc_lozenets:    'Лозенец, България',
        loc_svetivlas:   'Свети Влас, България',

        // index.html (hub)
        hub_h1:       'Температура на водата в Черно море',
        hub_subtitle: 'Температура на морската повърхност по Българското Черноморие — на живо и исторически данни',
        hub_map:      'Текуща температура на водата',
        hub_pick:     'Изберете локация',
        map_view:     'Към таблото',

        // index.html
        dash_h1:            'Табло',
        dash_subtitle:      'Температура на водата в Черно море — {location}',
        dash_stats_loading: 'Температура на тази дата (зареждане…)',
        dash_stats_title: 'Температура на {date} — последните 5 години',
        dash_last30:        'Последните 30 дни',
        dash_full:          'Пълна история',
        dash_full_tip:      'Мащабирайте или изберете диапазон по-долу, за да разгледате историческите данни.',

        // Location descriptions (dashboard)
        desc_burgas: "Най-големият град по южното Черноморие на България, Бургас е оживено пристанище и културен център, разположен между морето и поредица от спокойни крайбрежни езера, богати на птици. Елегантната му Морска градина се простира покрай брега и води към дълъг централен плаж и оживен пешеходен център, изпълнен с кафенета и галерии. Градът служи като главна врата към южните курорти, като същевременно предлага своя собствена спокойна, космополитна морска атмосфера.",
        desc_sinemorets: "Разположено дълбоко на юг в защитения природен парк Странджа, това село е богато на биоразнообразие и предлага суров, недокоснат пейзаж. То е дом на едни от най-красивите и уникални плажове в страната, където река Велека се влива в морето, образувайки зашеметяващи пясъчни коси. Историята му е дълбоко вкоренена в местните традиции на Странджанския край, което го прави отлична дестинация за тези, които искат да изследват дивата природа и спокойствието.",
        desc_varna: "Известна като „морската столица“ на България, този голям град е наследник на древно тракийско селище, а по-късно и римски балнеоложки център. Той се гордее с емблематични забележителности като Римските терми и обширната Морска градина, която се простира покрай огромните златни плажове на града. Градът предлага космополитна градска среда наред с лесен достъп до девствения морски бряг.",
        desc_kamenbryag: "Това отдалечено северно село е разположено върху стръмни крайбрежни скали и е прочуто с близкия археологически резерват Яйлата, с неговите древни пещерни жилища и скални гробници, издълбани в камъка. Вместо широки пясъчни плажове, брегът тук предлага драматични скални тераси, скрити заливчета и кристалночиста вода, предпочитана от водолази и свободолюбиви души. Той е най-известен с празнуването на Джулай морнинг, когато тълпи се събират на скалите, за да посрещнат първия изгрев на месеца.",
        desc_tyulenovo: "Кръстено на тюлените монаси, които някога са обитавали бреговете му, това мъничко рибарско село е прочуто със зрелищните си морски пещери, естествени скални арки и отвесни скали, спускащи се в дълбока, прозрачна вода. Тук няма традиционен плаж, но драматичният скалист бряг го е превърнал в притегателна точка за скокове от скали, катерачи и подводни изследователи. Тихият му чар на „края на света“ предлага недокоснато убежище далеч от претъпканите курорти на юг.",
        desc_nessebar: "Този обект на световното наследство на ЮНЕСКО е историческо съкровище с древен Стар град, разположен на полуостров, с църкви от византийската епоха и калдъръмени улички. Посетителите могат да разгледат богатата му история, преди да се насладят на модерните пясъчни плажове, които се простират покрай брега на новия град. Той съчетава по съвършен начин чара на древността с удобствата на съвременен морски курорт.",
        desc_sozopol: "Като един от най-старите градове в България, Созопол е прочут с романтичния си Стар град, изпълнен с традиционни дървени къщи от XIX век и тесни, криволичещи улички. Градът е обграден от красиви живописни плажове като Хармани и близките къмпинги, което го прави любимо място за тези, които обичат съчетанието между културно изследване и слънчеви бани. Спокойната му атмосфера и древните руини предлагат уникално морско изживяване.",
        desc_sunnybeach: "Най-големият и най-известен курорт в България, разработен като модерен ваканционен център, днес привлича хиляди с енергичния си нощен живот и развлечения. Курортът е прочут с широката си ивица от фин, окъпан в слънце пясък, която се простира на километри покрай брега. Това е първокласното място за тези, които търсят непрекъснато действие, водни спортове и оживени плажни барове.",
        desc_goldensands: "Този популярен северен курорт е обвит в легенди, според които пирати са заровили тук златно съкровище, превърнало се в характерния за курорта фин златист пясък. Той е заобиколен от пищен Национален парк, който се спуска към искрящото море, предлагайки идеално съчетание от природа и луксозен туризъм. Самият плаж е обширен и добре поддържан, привличайки посетители с минералните си извори и богатите курортни удобства.",
        desc_balchik: "Исторически значим със зашеметяващия си дворец, който е служил за лятна резиденция на румънската кралица Мария, градът съчетава средиземноморски и балкански архитектурни стилове. Той е особено прочут с екзотичната си ботаническа градина, която се спуска каскадно по скалите към водата. Местните плажове са по-малки и по-уютни, предлагайки тиха алтернатива на по-големите и оживени курорти.",
        desc_capekaliakra: "Този драматичен, тесен нос е значим археологически обект, дом на руините на древна средновековна крепост и богата на легенди история. Макар районът да се определя по-скоро от извисяващите се 70-метрови скали и панорамните морски гледки, отколкото от традиционен плаж, той предлага малки скрити заливчета в подножието на скалите. Това е първокласна дестинация за тези, които се интересуват от природа, миграция на птици и древна история.",
        desc_albena: "Създаден специално за туризъм, този курорт е ценен с организираната си, подходяща за семейства среда и пищния си парков пейзаж. Той разполага с широк плаж, отличен със „Син флаг“, известен с чистите си плитки води и фин пясък, което го прави изключително безопасен за деца. Целият комплекс е заобиколен от зеленина, предлагайки спокойна и добре поддържана атмосфера за класическа морска почивка.",
        desc_svetikonstantin: "Като най-старият курорт по българското крайбрежие, той носи наследство на здраве и е прочут с лечебните си минерални извори и термални басейни. Брегът тук е характерно скалист и уютен, с няколко малки, тихи и очарователни бутикови плажа, скрити сред дърветата. Това е идеална дестинация за тези, които търсят спокойна, ориентирана към СПА почивка далеч от тълпите.",
        desc_irakli: "Убежище за любителите на природата, това е един от малкото останали диви, незастроени плажове по крайбрежието, известен с девствената си красота и липсата на търговска инфраструктура. Историята му е свързана с недокоснатия пейзаж край село Емона, където Стара планина се среща с морето при нос Емине. Той остава любима дестинация за къмпингуващи и за търсещите спокойно, природно убежище.",
        desc_pomorie: "Този древен град е разположен на тесен скалист полуостров и е прочут със солниците си и лечебните си кални процедури, богати на минерали. Историята му датира от древността, като местни забележителности като тракийската „Куполна гробница“ показват дълбоките културни корени на региона. Плажовете тук са уникални, често с тъмен, богат на минерали пясък и спокойни води, идеални за здравен туризъм.",
        desc_primorsko: "Първоначално малко рибарско селище, този град се е превърнал в оживен младежки курорт с непринуден, провинциален чар. Той е разположен на нос, който предлага два отделни, обширни и чисти пясъчни плажа — един на север и един на юг. Той е широко предпочитан заради достъпното настаняване, оживения нощен живот и красивите си природни дюни.",
        desc_lozenets: "Някога сънливо рибарско селце, Лозенец се е превърнал в стилна, модна дестинация, известна с непринудената си „бохемска“ атмосфера. Районът разполага с няколко красиви златисти плажа, популярни както сред младите семейства, така и сред по-младата компания. Той остава предпочитано място за тези, които искат съчетание от модерни плажни барове и спокойна крайбрежна атмосфера.",
        desc_svetivlas: "Този град е исторически значим като тихо селище, превърнало се в първокласна луксозна дестинация за яхтинг с огромна модерна марина. Той е разположен в подножието на Стара планина, предлагайки красив контраст между зелените склонове и тъмносиньото море. Плажовете му са добре поддържани и предлагат малко по-изискано, спокойно изживяване в сравнение с оживения му съсед Слънчев бряг.",

        // compare.html
        cmp_h1:        'Сравнение по години',
        cmp_subtitle:  'Наложете избрани години по ос ян.–дек., за да откриете сезонни модели',
        cmp_from:      'От',
        cmp_to:        'До',
        cmp_smooth:    'Изглаждане (7-дневна ср.)',
        cmp_timeline:  'Избор по времева линия',
        cmp_tip:       'Плъзнете, за да изберете период — обновява отметките за години горе.',

        // compare-locations.html
        cl_h1:           'Сравнение на локации',
        cl_subtitle:     'Наложете температурата на водата за различни градове по Черноморието',
        cl_smooth:       'Изглаждане (7-дневна ср.)',
        cl_timeline_h2:  'През годините',
        cl_timeline_tip: 'Всяка линия е локация за целия период. Превключвайте градовете горе.',
        cl_seasonal_h2:  'Сезонно (една година)',
        cl_seasonal_tip: 'Само избраната година, по ос ян.–дек. за сравнение на сезоните.',
        cl_year:         'Година',

        // heatmap.html
        hm_h1:         'Месечна топлинна карта',
        hm_subtitle:   'Средна температура на водата по месеци за всички години ({year} – днес)',
        hm_monthly:    'Месечни средни по години',
        hm_tip:        'Всяка клетка показва средната температура за този месец/година. Посочете за точни стойности.',

        // stats.html
        st_h1:          'Статистика и рекорди',
        st_subtitle:    'Рекорди за всички времена и годишна статистика от {year} г.',
        st_records:     'Рекорди за всички времена',
        st_annual:      'Годишни мин / ср / макс',
        st_trend:       'Дългосрочна тенденция',
        st_trend_tip:   'Годишна средна стойност с линия на 5-годишна плъзгаща средна.',
        st_hottest:     'Най-висока отчетена',
        st_coldest:     'Най-ниска отчетена',
        st_warmest_yr:  'Най-топла година (ср.)',
        st_coldest_yr:  'Най-студена година (ср.)',
        st_max:         'Макс',
        st_avg:         'Ср',
        st_min:         'Мин',
        st_yearly_avg:  'Годишна средна',
        st_trend_5yr:   '5-год. тенденция',

        months: ['Яну','Фев','Мар','Апр','Май','Юни','Юли','Авг','Сеп','Окт','Ное','Дек'],
    },
};

function getLang() {
    const saved = localStorage.getItem('lang');
    if (saved === 'en' || saved === 'bg') return saved;
    return (navigator.language || 'en').toLowerCase().startsWith('bg') ? 'bg' : 'en';
}

function t(key) {
    const lang = getLang();
    const val = (I18N[lang] && I18N[lang][key]);
    return val !== undefined ? val : (I18N.en[key] !== undefined ? I18N.en[key] : key);
}

function setLang(lang) {
    localStorage.setItem('lang', lang);
    location.reload();
}

function applyStaticTranslations() {
    document.documentElement.lang = getLang();
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        el.innerHTML = t(el.dataset.i18nHtml);
    });
    const titleEl = document.querySelector('title[data-i18n-title]');
    if (titleEl) document.title = t(titleEl.dataset.i18nTitle);
}

function renderSwitcher() {
    const container = document.querySelector('.lang-switch');
    if (!container) return;
    const lang = getLang();
    const flags = [
        { code: 'en', flag: '🇬🇧', label: 'English' },
        { code: 'bg', flag: '🇧🇬', label: 'Български' },
    ];
    container.innerHTML = '';
    flags.forEach(f => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'lang-btn' + (f.code === lang ? ' active' : '');
        btn.textContent = f.flag;
        btn.title = f.label;
        btn.setAttribute('aria-label', f.label);
        btn.addEventListener('click', () => setLang(f.code));
        container.appendChild(btn);
    });
}

function renderNavToggle() {
    const inner = document.querySelector('.nav-inner');
    if (!inner || inner.querySelector('.nav-toggle')) return;
    const nav = inner.closest('.nav');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-toggle';
    btn.textContent = '☰';
    btn.setAttribute('aria-label', t('nav_menu'));
    btn.setAttribute('aria-expanded', 'false');
    const close = () => {
        nav.classList.remove('nav-open');
        btn.setAttribute('aria-expanded', 'false');
    };
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const open = nav.classList.toggle('nav-open');
        btn.setAttribute('aria-expanded', String(open));
    });
    // Close when a menu link is tapped or when clicking outside the nav.
    inner.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('click', (e) => {
        if (!nav.contains(e.target)) close();
    });
    inner.appendChild(btn);
}

document.addEventListener('DOMContentLoaded', () => {
    applyStaticTranslations();
    renderSwitcher();
    renderNavToggle();
});
