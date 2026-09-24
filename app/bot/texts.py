"""Bot UI strings. Seller languages without their own UI fall back (kk/uz -> ru, tr -> en)."""
from __future__ import annotations

SELLER_LANGS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "zh": "🇨🇳 中文", "tr": "🇹🇷 Türkçe",
                "kk": "🇰🇿 Қазақша", "uz": "🇺🇿 Oʻzbekcha"}
UI_FALLBACK = {"kk": "ru", "uz": "ru", "tr": "en"}

T: dict[str, dict[str, str]] = {
    "ru": {
        "choose_lang": "Выберите язык. На нём вы будете читать отзывы и писать ответы — покупателю ответ уйдёт на его языке.",
        "help": ("<b>Ответы покупателям Wildberries, Ozon и Яндекс Маркета на любом языке.</b>\n\n"
                 "Я забираю новые отзывы и вопросы, перевожу их на ваш язык и готовлю ответ на языке покупателя. "
                 "Вы нажимаете «Отправить» — ответ публикуется на маркетплейсе.\n\n"
                 "/connect — подключить магазин\n/accounts — мои магазины\n"
                 "/card — карточка товара на русском из описания на любом языке\n"
                 "/facts — факты о товарах для точных ответов\n/sync — проверить новые сейчас\n"
                 "/settings — автоответы, подпись, язык\n/help — эта справка\n\n"
                 "Попробуйте без ключей: /connect → Demo."),
        "connect_choose": "Какой маркетплейс подключаем?",
        "ask_wildberries": ("Пришлите токен Wildberries одним сообщением.\n\nГде взять: ЛК продавца → Настройки → "
                            "Доступ к API → Создать токен, категория <b>«Вопросы и отзывы»</b>.\n"
                            "Сообщение с токеном я сразу удалю из чата."),
        "ask_ozon": ("Пришлите <b>Client-Id</b> и <b>Api-Key</b> Ozon через пробел.\n\nГде взять: ЛК Ozon → Настройки → "
                     "Seller API.\n⚠️ Ozon открывает отзывы и вопросы по API только с подпиской Premium Plus/Pro.\n"
                     "Сообщение с ключом я сразу удалю."),
        "ask_yandex_market": ("Пришлите <b>API-ключ</b> и <b>ID кабинета (businessId)</b> Яндекс Маркета через пробел.\n\n"
                              "Где взять: ЛК → Настройки → API и модули → API-ключ с доступом к отзывам.\n"
                              "Пока подключаются только отзывы; вопросы — в следующей версии.\nСообщение с ключом я сразу удалю."),
        "bad_format": "Не похоже на ключ в нужном формате. Попробуйте ещё раз или /cancel.",
        "checking": "Проверяю доступ…",
        "connected": "✅ {mp} подключён. Забираю новые отзывы и вопросы…",
        "connect_failed": "❌ Не получилось подключить: {error}",
        "no_accounts": "Магазинов пока нет. /connect",
        "accounts": "Ваши магазины:",
        "acc_line": "{mp} #{id} — {state}",
        "acc_ok": "работает", "acc_off": "⛔ отключён: {error}",
        "btn_remove": "Удалить {mp} #{id}",
        "removed": "Удалено.",
        "settings": ("<b>Настройки</b>\nЯзык: {lang}\nПодпись: {signature}\nАвтоответ: {auto}\n"
                     "Автоответ на вопросы: {autoq}\nЛимит ИИ-ответов: {used}/{limit} в этом месяце"),
        "auto_off": "выключен", "auto_n": "на отзывы от {n}★ без вопросов к фактам",
        "btn_auto_off": "Автоответ: выкл", "btn_auto_5": "Авто: только 5★", "btn_auto_4": "Авто: 4–5★",
        "btn_signature": "Подпись", "btn_lang": "Язык",
        "ask_signature": "Пришлите подпись для ответов (например: «Команда магазина Уютный дом»). «-» — без подписи.",
        "saved": "Сохранено.",
        "sync_started": "Проверяю новые отзывы и вопросы…",
        "sync_done": "Готово. Новых: {n}.",
        "no_accounts_sync": "Сначала подключите магазин: /connect",
        "quota_exceeded": "Лимит {limit} ИИ-ответов в этом месяце исчерпан. Новые отзывы подождут — напишите нам для расширения.",
        "account_disabled": "⛔ {mp}: доступ отклонён, я остановил проверку.\n{error}\nПодключите заново: /connect",
        "review": "Отзыв", "question": "Вопрос",
        "original": "Покупатель", "translation": "Перевод", "draft": "Ответ ({bl})", "draft_tr": "Перевод ответа",
        "no_text": "(без текста, только оценка)",
        "needs_input": "⚠️ Нужны ваши данные о товаре — нажмите «Изменить» и допишите ответ.",
        "st_sent": "✅ Отправлено", "st_auto_sent": "🤖 Отправлено автоматически", "st_skipped": "⏭ Пропущено",
        "btn_send": "✅ Отправить", "btn_edit": "✏️ Изменить", "btn_regen": "🔄 Другой вариант", "btn_skip": "⏭ Пропустить",
        "ask_edit": "Напишите ответ на своём языке — я переведу его для покупателя и покажу перед отправкой.",
        "send_failed": "❌ Маркетплейс не принял ответ: {error}",
        "ai_failed": "❌ ИИ не смог подготовить текст, попробуйте ещё раз: {error}",
        "cancelled": "Отменено.",
        "not_found": "Не найдено.",
        "btn_facts": "📚 Добавить факты",
        "ask_item_facts": "Напишите факты о товаре «{product}» ({sku}) на своём языке: материал, размеры, совместимость, уход, комплект. Я запомню их и перепишу ответ, а следующие вопросы по этому товару будут отвечаться сразу.",
        "facts_help": "<b>Факты о товарах</b>\nИз них бот точно отвечает на вопросы покупателей. Пишите на любом языке.\n\n• Добавить: первая строка — артикул (nmId / SKU / offerId), дальше факты.\n• О магазине в целом (доставка, гарантия, возврат): первая строка <code>*</code>.\n• Удалить: <code>артикул -</code>\n• Много товаров: пришлите CSV-файл с колонками <code>артикул;название;факты</code>.\n\nСохранено: {n}. {skus}",
        "facts_saved": "✅ Факты сохранены для {sku}.",
        "facts_deleted": "Удалено: {sku}.",
        "facts_bad": "Первая строка — артикул, со второй — факты. Или /cancel.",
        "csv_loaded": "✅ Загружено товаров: {n}. Пропущено строк: {bad}.",
        "csv_bad": "Не удалось прочитать CSV (нужны колонки артикул;название;факты): {error}",
        "autoq_on": "включён — если факты о товаре покрывают ответ",
        "autoq_off": "выключен",
        "btn_autoq": "Автоответ на вопросы: вкл/выкл",
        "card_ask": "Опишите товар на любом языке: что это, материалы, размеры, особенности, для кого, комплектация. Чем больше фактов, тем сильнее карточка — я ничего не выдумываю.",
        "card_wait": "Пишу карточку…",
        "card_title": "Название",
        "card_desc": "Описание",
        "card_kw": "Поисковые запросы",
        "card_attrs": "Характеристики",
        "card_missing": "Добавьте, чтобы карточка продавала лучше",
        "card_note": "Нажмите на текст, чтобы скопировать.",
        "btn_save_facts": "💾 Сохранить как факты товара",
        "ask_sku": "Пришлите артикул товара (nmId / SKU / offerId), к которому привязать это описание.",
    },
    "en": {
        "choose_lang": "Choose your language. You will read reviews and write replies in it — the buyer gets the reply in their own language.",
        "help": ("<b>Answer Wildberries, Ozon and Yandex Market buyers in any language.</b>\n\n"
                 "I fetch new reviews and questions, translate them into your language and draft a reply in the buyer's "
                 "language. You tap “Send” and the reply is published on the marketplace.\n\n"
                 "/connect — connect a shop\n/accounts — my shops\n"
                 "/card — Russian product card from a description in any language\n"
                 "/facts — product facts for accurate answers\n/sync — check for new items now\n"
                 "/settings — auto-replies, signature, language\n/help — this help\n\n"
                 "Try it without keys: /connect → Demo."),
        "connect_choose": "Which marketplace?",
        "ask_wildberries": ("Send your Wildberries token in one message.\n\nWhere: seller cabinet → Settings → API access → "
                            "create a token with the <b>“Questions and reviews”</b> category.\nI will delete the message right away."),
        "ask_ozon": ("Send your Ozon <b>Client-Id</b> and <b>Api-Key</b> separated by a space.\n\nWhere: Ozon cabinet → "
                     "Settings → Seller API.\n⚠️ Ozon only exposes reviews and questions via API with Premium Plus/Pro.\n"
                     "I will delete the message right away."),
        "ask_yandex_market": ("Send your Yandex Market <b>API key</b> and <b>businessId</b> separated by a space.\n\n"
                              "Where: cabinet → Settings → API and modules → API key with access to reviews.\n"
                              "Only reviews for now; questions come in the next version.\nI will delete the message right away."),
        "bad_format": "This doesn't look like a key in the right format. Try again or /cancel.",
        "checking": "Checking access…",
        "connected": "✅ {mp} connected. Fetching new reviews and questions…",
        "connect_failed": "❌ Could not connect: {error}",
        "no_accounts": "No shops yet. /connect",
        "accounts": "Your shops:",
        "acc_line": "{mp} #{id} — {state}",
        "acc_ok": "active", "acc_off": "⛔ disabled: {error}",
        "btn_remove": "Remove {mp} #{id}",
        "removed": "Removed.",
        "settings": ("<b>Settings</b>\nLanguage: {lang}\nSignature: {signature}\nAuto-reply: {auto}\n"
                     "Auto-answer questions: {autoq}\nAI replies this month: {used}/{limit}"),
        "auto_off": "off", "auto_n": "reviews with {n}★ or more, when no product facts are needed",
        "btn_auto_off": "Auto-reply: off", "btn_auto_5": "Auto: 5★ only", "btn_auto_4": "Auto: 4–5★",
        "btn_signature": "Signature", "btn_lang": "Language",
        "ask_signature": "Send a signature for replies (e.g. “Cosy Home team”). Send “-” for none.",
        "saved": "Saved.",
        "sync_started": "Checking for new reviews and questions…",
        "sync_done": "Done. New: {n}.",
        "no_accounts_sync": "Connect a shop first: /connect",
        "quota_exceeded": "You have used all {limit} AI replies this month. New reviews will wait — contact us to extend.",
        "account_disabled": "⛔ {mp}: access denied, I stopped checking.\n{error}\nReconnect: /connect",
        "review": "Review", "question": "Question",
        "original": "Buyer", "translation": "Translation", "draft": "Reply ({bl})", "draft_tr": "Reply translation",
        "no_text": "(no text, rating only)",
        "needs_input": "⚠️ Needs your product facts — tap “Edit” and complete the reply.",
        "st_sent": "✅ Sent", "st_auto_sent": "🤖 Sent automatically", "st_skipped": "⏭ Skipped",
        "btn_send": "✅ Send", "btn_edit": "✏️ Edit", "btn_regen": "🔄 Another version", "btn_skip": "⏭ Skip",
        "ask_edit": "Write the reply in your language — I will translate it for the buyer and show it before sending.",
        "send_failed": "❌ The marketplace rejected the reply: {error}",
        "ai_failed": "❌ AI could not prepare the text, please try again: {error}",
        "cancelled": "Cancelled.",
        "not_found": "Not found.",
        "btn_facts": "📚 Add facts",
        "ask_item_facts": "Write facts about “{product}” ({sku}) in your language: material, size, compatibility, care, what's in the box. I will remember them and rewrite the reply; future questions about this product will be answered right away.",
        "facts_help": "<b>Product facts</b>\nThe bot uses them to answer buyer questions accurately. Any language.\n\n• Add: first line is the SKU (nmId / SKU / offerId), then the facts.\n• Shop-wide facts (delivery, warranty, returns): first line <code>*</code>.\n• Delete: <code>SKU -</code>\n• Many products: send a CSV file with columns <code>sku;name;facts</code>.\n\nSaved: {n}. {skus}",
        "facts_saved": "✅ Facts saved for {sku}.",
        "facts_deleted": "Deleted: {sku}.",
        "facts_bad": "First line is the SKU, facts from the second line. Or /cancel.",
        "csv_loaded": "✅ Products loaded: {n}. Rows skipped: {bad}.",
        "csv_bad": "Could not read the CSV (columns sku;name;facts expected): {error}",
        "autoq_on": "on — when product facts cover the answer",
        "autoq_off": "off",
        "btn_autoq": "Auto-answer questions: on/off",
        "card_ask": "Describe the product in any language: what it is, materials, size, features, who it is for, what's in the box. More facts make a stronger card — I never make things up.",
        "card_wait": "Writing the card…",
        "card_title": "Title",
        "card_desc": "Description",
        "card_kw": "Search queries",
        "card_attrs": "Characteristics",
        "card_missing": "Add these to sell better",
        "card_note": "Tap a text to copy it.",
        "btn_save_facts": "💾 Save as product facts",
        "ask_sku": "Send the product SKU (nmId / SKU / offerId) to attach this description to.",
    },
    "zh": {
        "choose_lang": "请选择语言。您将用该语言阅读评价和撰写回复，买家会收到其本人语言的回复。",
        "help": ("<b>用任何语言回复 Wildberries、Ozon 和 Yandex Market 的买家。</b>\n\n"
                 "我会获取新的评价和问题，翻译成您的语言，并用买家的语言起草回复。"
                 "您点击“发送”，回复即发布到平台。\n\n"
                 "/connect — 连接店铺\n/accounts — 我的店铺\n"
                 "/card — 用任何语言的描述生成俄语商品卡\n"
                 "/facts — 商品信息，用于准确回答\n/sync — 立即检查新消息\n"
                 "/settings — 自动回复、签名、语言\n/help — 帮助\n\n"
                 "无需密钥即可试用：/connect → Demo。"),
        "connect_choose": "要连接哪个平台？",
        "ask_wildberries": ("请在一条消息中发送 Wildberries 令牌。\n\n获取方式：卖家后台 → 设置 → API 访问 → "
                            "创建令牌，类别选择 <b>“问题和评价”</b>。\n我会立即删除这条消息。"),
        "ask_ozon": ("请发送 Ozon 的 <b>Client-Id</b> 和 <b>Api-Key</b>，用空格分隔。\n\n获取方式：Ozon 后台 → 设置 → Seller API。\n"
                     "⚠️ 只有订阅 Premium Plus/Pro 的卖家才能通过 API 获取评价和问题。\n我会立即删除这条消息。"),
        "ask_yandex_market": ("请发送 Yandex Market 的 <b>API 密钥</b> 和 <b>businessId</b>，用空格分隔。\n\n"
                              "获取方式：后台 → 设置 → API 和模块 → 具有评价权限的 API 密钥。\n"
                              "目前仅支持评价，问题将在下一版本中支持。\n我会立即删除这条消息。"),
        "bad_format": "格式似乎不正确。请重试或发送 /cancel。",
        "checking": "正在检查访问权限…",
        "connected": "✅ {mp} 已连接。正在获取新的评价和问题…",
        "connect_failed": "❌ 连接失败：{error}",
        "no_accounts": "还没有店铺。/connect",
        "accounts": "您的店铺：",
        "acc_line": "{mp} #{id} — {state}",
        "acc_ok": "运行中", "acc_off": "⛔ 已停用：{error}",
        "btn_remove": "删除 {mp} #{id}",
        "removed": "已删除。",
        "settings": ("<b>设置</b>\n语言：{lang}\n签名：{signature}\n自动回复：{auto}\n自动回答问题：{autoq}\n本月 AI 回复：{used}/{limit}"),
        "auto_off": "关闭", "auto_n": "{n}★ 及以上且无需商品信息的评价",
        "btn_auto_off": "自动回复：关", "btn_auto_5": "自动：仅 5★", "btn_auto_4": "自动：4–5★",
        "btn_signature": "签名", "btn_lang": "语言",
        "ask_signature": "请发送回复签名（例如“舒适家居团队”）。发送“-”表示不使用签名。",
        "saved": "已保存。",
        "sync_started": "正在检查新的评价和问题…",
        "sync_done": "完成。新增：{n}。",
        "no_accounts_sync": "请先连接店铺：/connect",
        "quota_exceeded": "本月 {limit} 条 AI 回复额度已用完。新评价将等待处理，如需扩容请联系我们。",
        "account_disabled": "⛔ {mp}：访问被拒绝，已停止检查。\n{error}\n请重新连接：/connect",
        "review": "评价", "question": "问题",
        "original": "买家", "translation": "翻译", "draft": "回复（{bl}）", "draft_tr": "回复翻译",
        "no_text": "（无文字，仅评分）",
        "needs_input": "⚠️ 需要您提供商品信息——请点击“修改”补充回复。",
        "st_sent": "✅ 已发送", "st_auto_sent": "🤖 已自动发送", "st_skipped": "⏭ 已跳过",
        "btn_send": "✅ 发送", "btn_edit": "✏️ 修改", "btn_regen": "🔄 换一个", "btn_skip": "⏭ 跳过",
        "ask_edit": "请用您的语言写回复——我会翻译给买家，并在发送前给您确认。",
        "send_failed": "❌ 平台未接受回复：{error}",
        "ai_failed": "❌ AI 未能生成文本，请重试：{error}",
        "cancelled": "已取消。",
        "not_found": "未找到。",
        "btn_facts": "📚 添加商品信息",
        "ask_item_facts": "请用您的语言填写商品“{product}”（{sku}）的信息：材质、尺寸、兼容性、保养、包装清单。我会记住并重写回复，以后关于该商品的问题将立即回答。",
        "facts_help": "<b>商品信息</b>\n机器人据此准确回答买家问题。可使用任何语言。\n\n• 添加：第一行为货号（nmId / SKU / offerId），之后为商品信息。\n• 店铺通用信息（配送、保修、退货）：第一行写 <code>*</code>。\n• 删除：<code>货号 -</code>\n• 批量：发送 CSV 文件，列为 <code>货号;名称;信息</code>。\n\n已保存：{n}。{skus}",
        "facts_saved": "✅ 已保存 {sku} 的商品信息。",
        "facts_deleted": "已删除：{sku}。",
        "facts_bad": "第一行为货号，第二行起为商品信息。或发送 /cancel。",
        "csv_loaded": "✅ 已导入商品：{n}。跳过行数：{bad}。",
        "csv_bad": "无法读取 CSV（需要列：货号;名称;信息）：{error}",
        "autoq_on": "开启——当商品信息足以回答时",
        "autoq_off": "关闭",
        "btn_autoq": "自动回答问题：开/关",
        "card_ask": "请用任何语言描述商品：是什么、材质、尺寸、特点、适用人群、包装清单。信息越多，商品卡越好——我不会编造内容。",
        "card_wait": "正在撰写商品卡…",
        "card_title": "标题",
        "card_desc": "描述",
        "card_kw": "搜索关键词",
        "card_attrs": "商品属性",
        "card_missing": "补充以下信息可提升销量",
        "card_note": "点击文字即可复制。",
        "btn_save_facts": "💾 保存为商品信息",
        "ask_sku": "请发送要关联此描述的商品货号（nmId / SKU / offerId）。",
    },
}


def t(lang: str, key: str, /, **kw) -> str:
    ui = lang if lang in T else UI_FALLBACK.get(lang, "en")
    return T[ui][key].format(**kw) if kw else T[ui][key]
