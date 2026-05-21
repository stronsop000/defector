"""Seed the DB with synthetic but realistic (review + classification) pairs
so the dashboard has populated clusters before the real classify run finishes.

All seeded rows use review_id prefix `demo:` so they're trivially identifiable
and removable.

Usage:
    python -m scripts.seed_demo_data            # insert ~80 demo entries
    python -m scripts.seed_demo_data --purge    # remove all demo:* rows
    python -m scripts.seed_demo_data --replace  # purge then re-insert

The seed data is organized into ~15 cluster themes, each with 4-6 variations,
so the synthesize.py `volume >= 3` threshold is satisfied and the dashboard
shows meaningful patterns rather than singletons.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import connect  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("seed")

MODEL_TAG = "demo-seed-v1"
NOW = datetime.now()


def _date(days_ago: int) -> datetime:
    return NOW - timedelta(days=days_ago)


# Each cluster theme is one (app, category, market, lang, sentiment) combo with N variations.
# variation tuples: (rating, title, body, sub_reason, churn, quote)
# sentiment defaults to 'negative' for backward compatibility.
CLUSTERS = [
    # ---------- Lovevery / price_value / US ----------
    dict(
        app="Lovevery", cat="competitor", country="us", lang="en", category_key="price_value",
        variations=[
            (1, "Way too expensive", "Eighty dollars a kit is insane for what amounts to a few wooden toys and a PDF. Cancelled after one shipment.", "kit price too high", True, "Eighty dollars a kit is insane"),
            (2, "Not worth subscription", "The play kits look nice but the per-kit value just isnt there once you actually use them. Could buy the same things on Amazon for half.", "kit not worth price", False, "the value just isnt there"),
            (1, "Surprise charge", "Got charged for the next kit a week after cancellation. Refund took 6 emails. Predatory billing on a premium price.", "billed after cancel", True, "got charged a week after cancellation"),
            (2, "Premium app is paywalled", "Bought the kits expecting full app access but most features are behind ANOTHER subscription. Double dipping.", "double subscription paywall", False, "most features are behind another subscription"),
            (1, "Annual auto-renewed", "Annual subscription auto-renewed without notification at $200. No reminder email, no way to refund. This should be illegal.", "auto-renew no warning", True, "auto-renewed without notification"),
        ],
    ),
    # ---------- Lovevery / content_quality / US ----------
    dict(
        app="Lovevery", cat="competitor", country="us", lang="en", category_key="content_quality",
        variations=[
            (2, "Activities are basic", "The activities are things any parent already does. Stack the blocks. Roll the ball. For this price I expected actual research-backed depth.", "basic activities", False, "things any parent already does"),
            (2, "Repetitive", "Same five activities recycled month after month with different names. Felt like padding.", "repetitive content", False, "same five activities recycled month after month"),
            (1, "No real research", "Marketing says 'developed by experts' but the activities have no citations and feel like blog posts. Where is the research?", "no research citations", False, "no citations and feel like blog posts"),
            (2, "Toddler content drops off", "Quality was fine for infants but the toddler stages feel rushed. Same toys recycled into 'new' activities.", "weak toddler content", False, "toddler stages feel rushed"),
        ],
    ),
    # ---------- BabySparks / bugs_crashes / US ----------
    dict(
        app="BabySparks", cat="competitor", country="us", lang="en", category_key="bugs_crashes",
        variations=[
            (1, "Crashes constantly", "App crashes every time I open a video activity. Reinstalled twice. Lost all my baby's milestone log.", "video crash", True, "crashes every time I open a video"),
            (1, "Wont load", "Stuck on the splash screen for the last week. Tried clearing cache, reinstalling, nothing works.", "splash screen freeze", False, "stuck on the splash screen for the last week"),
            (2, "Data wiped after update", "The v6 update wiped all my logged milestones. Months of careful tracking gone. Support says they cant recover.", "data wiped on update", True, "wiped all my logged milestones"),
            (1, "Sync broken", "Logging on iPhone doesnt show up on iPad. Used to work. Stopped after last update.", "cross-device sync broken", False, "doesnt show up on iPad"),
            (1, "Login loop", "Cant log in. Keeps cycling between password screen and 'session expired'. Useless.", "login loop", True, "keeps cycling between password screen and session expired"),
        ],
    ),
    # ---------- BabyCenter / localization / Brazil ----------
    dict(
        app="BabyCenter", cat="competitor", country="br", lang="pt", category_key="localization",
        variations=[
            (2, "Traducao horrivel", "A traducao para portugues e robotica e cheia de erros. Parece tradutor automatico.", "machine-translated content", False, "traducao para portugues e robotica e cheia de erros"),
            (2, "Conteudo americano", "Os artigos sao todos baseados no sistema de saude americano. Vacinas, datas de marcos, recomendacoes — nada bate com o que meu pediatra fala aqui.", "us-only content", False, "todos baseados no sistema de saude americano"),
            (1, "Nao adapta para regiao", "A app sabe que estou no Brasil mas insiste em recomendar produtos que nao existem aqui. Inutil.", "us-only product recs", False, "recomendar produtos que nao existem aqui"),
            (2, "Datas erradas", "Marcos de desenvolvimento e calendario de vacinas estao no padrao americano. Confunde mais do que ajuda.", "wrong milestone dates", False, "no padrao americano"),
        ],
    ),
    # ---------- Wonder Weeks / trust_credibility / US ----------
    dict(
        app="The Wonder Weeks", cat="competitor", country="us", lang="en", category_key="trust_credibility",
        variations=[
            (1, "Debunked science", "The mental leaps theory has been debunked by multiple peer-reviewed studies. App cites no real research.", "debunked theory", False, "debunked by multiple peer-reviewed studies"),
            (2, "No citations anywhere", "Beautiful UI but every claim is unsourced. As an academic I find this irresponsible to sell to anxious parents.", "no source citations", False, "every claim is unsourced"),
            (1, "Contradicts pediatrician", "Half the recommendations contradict what our pediatrician told us. Whose advice should I trust?", "conflicts with pediatrician", False, "contradicts what our pediatrician told us"),
            (2, "Pseudoscience vibes", "Reads like a horoscope for babies. 'Your baby will be fussy this week.' All babies are fussy every week.", "horoscope-like predictions", False, "reads like a horoscope for babies"),
        ],
    ),
    # ---------- Pampers Rewards / customer_support / US ----------
    dict(
        app="Pampers Rewards", cat="brand_product", country="us", lang="en", category_key="customer_support",
        variations=[
            (1, "No human will help", "Scanned 60 packs and lost half my points. Emailed support 4 times in 3 weeks, only bot responses.", "bot-only support", True, "only bot responses"),
            (1, "Lost my points", "Hundreds of points just vanished from my account. Support says 'expired' but I just got them last month. No appeal process.", "points expired unfairly", False, "hundreds of points just vanished"),
            (2, "Refund refused", "Damaged item from rewards catalog. They refused to replace or refund. Lost a months worth of scanning.", "no refund on damaged reward", False, "refused to replace or refund"),
            (1, "Account locked", "Account locked for 'suspicious activity' — I bought diapers and scanned them, thats it. Two weeks to unlock, with multiple identity submissions.", "wrongful account lock", True, "account locked for suspicious activity"),
        ],
    ),
    # ---------- Huggies Rewards / bugs_crashes / US ----------
    dict(
        app="Huggies Rewards", cat="brand_product", country="us", lang="en", category_key="bugs_crashes",
        variations=[
            (1, "Scanner broken", "Receipt scanner fails on 8 out of 10 receipts. Manual entry takes 5 minutes each.", "scanner fails on most receipts", False, "fails on 8 out of 10 receipts"),
            (1, "App crashes on submit", "Every time I try to submit a receipt the app crashes. Lost a months worth.", "crashes on submit", True, "every time I try to submit a receipt the app crashes"),
            (2, "Page errors out", "Redemption page errors out 'something went wrong' for two weeks now. Cant cash in.", "redemption page broken", False, "errors out something went wrong"),
            (1, "OCR loses info", "Scanner reads the brand wrong half the time. Bought Huggies, app says Pampers, no points.", "OCR misreads brand", False, "reads the brand wrong half the time"),
        ],
    ),
    # ---------- Kinedu / price_value / Mexico ----------
    dict(
        app="Kinedu", cat="kinedu", country="mx", lang="es", category_key="price_value",
        variations=[
            (1, "Muy caro", "Pague la anual y me siguen mostrando anuncios de planes mas caros. Notificaciones cada 2 horas para que pague mas.", "upsell after paying", True, "anuncios de planes mas caros despues de pagar"),
            (2, "No vale el precio", "Para lo que dan, el precio mensual es excesivo. Hay apps gratuitas con casi el mismo contenido.", "overpriced vs free options", False, "el precio mensual es excesivo"),
            (1, "Cobro sorpresa", "Me cobraron despues del 'periodo de prueba' sin avisar. No hay forma facil de cancelar dentro de la app.", "trial converted without notice", True, "cobraron despues del periodo de prueba sin avisar"),
            (2, "Renovacion oculta", "Renovo automaticamente sin recordatorio. No me llego ningun aviso por correo.", "silent auto-renewal", False, "renovo automaticamente sin recordatorio"),
        ],
    ),
    # ---------- Huckleberry / ux_friction / US ----------
    dict(
        app="Huckleberry", cat="tracker", country="us", lang="en", category_key="ux_friction",
        variations=[
            (1, "Too many taps", "Logging a feed used to be one tap. Now its 4 taps and a popup. Why?", "logging takes too many taps", False, "logging a feed used to be one tap"),
            (2, "Cluttered home screen", "Home screen has gotten busier and busier with each update. Cant find the timer anymore.", "cluttered redesign", False, "home screen has gotten busier"),
            (1, "Confirm popups", "Every action requires a confirm popup. Confirm sleep start. Confirm sleep end. Confirm nap. Im operating one-handed at 3am.", "excessive confirm popups", False, "every action requires a confirm popup"),
            (2, "Hard to edit", "Editing a past log requires 5 screens. Used to be 2.", "editing now harder", False, "editing a past log requires 5 screens"),
        ],
    ),
    # ---------- Glow Baby / features_breadth / US ----------
    dict(
        app="Glow Baby", cat="tracker", country="us", lang="en", category_key="features_breadth",
        variations=[
            (2, "No partner sync", "Husband cant see what I logged. Multi-caregiver should be standard in 2026.", "no multi-caregiver sync", False, "husband cant see what I logged"),
            (2, "No offline mode", "Need internet to log a feeding? Useless on flights, useless during outages.", "no offline mode", False, "need internet to log a feeding"),
            (1, "Cant export", "Pediatrician asked for a sleep export. There is no export. Manually transcribed 3 months.", "no data export", False, "there is no export"),
            (2, "No twin support", "Twin parents have to keep two accounts. Awkward and error-prone. Just add a 'twins' toggle.", "no twin support", False, "twin parents have to keep two accounts"),
        ],
    ),
    # ---------- Ovia Pregnancy / privacy_data / US ----------
    dict(
        app="Ovia Pregnancy", cat="pregnancy", country="us", lang="en", category_key="privacy_data",
        variations=[
            (1, "Sells your data", "Within a week of signup I got targeted ads for formula and baby gear across every site. Coincidence? They share with 'partners' you cant opt out of.", "data sharing with partners", True, "share with partners you cant opt out of"),
            (1, "Cant delete account", "There is no way to delete your account from inside the app. Tried email, no response.", "no account deletion", True, "no way to delete your account from inside the app"),
            (2, "Permissions overreach", "Why does a pregnancy app need contacts and 24/7 location?", "excessive permissions", False, "why does a pregnancy app need contacts and 24/7 location"),
            (1, "HIPAA-like data shared", "Logged miscarriage details in app. Started getting ads for grief support and fertility clinics. Vile.", "sensitive data leaked to ads", True, "started getting ads for grief support after logging miscarriage"),
        ],
    ),
    # ---------- Lingokids / notifications_ads / US ----------
    dict(
        app="Lingokids", cat="early_education", country="us", lang="en", category_key="notifications_ads",
        variations=[
            (2, "Ads in paid app", "I pay for premium. Still get full-screen popups every 3 minutes pushing the 'family bundle'.", "upsells in paid tier", False, "full-screen popups every 3 minutes"),
            (1, "Push notification spam", "8 push notifications a day. From a kids app. Disabled all but they keep finding new categories to enable.", "push notification spam", False, "8 push notifications a day"),
            (2, "Constant upsells", "Every screen has a 'try premium' badge even on the premium tier. What are you upselling me to?", "endless upsell badges", False, "every screen has a try premium badge"),
            (1, "Email flood", "I get 4 marketing emails per week and the unsubscribe link goes to a 404.", "marketing email flood", False, "4 marketing emails per week"),
        ],
    ),
    # ---------- Khan Academy Kids / localization / Colombia ----------
    dict(
        app="Khan Academy Kids", cat="early_education", country="co", lang="es", category_key="localization",
        variations=[
            (2, "Casi todo en ingles", "La interfaz esta en espanol pero la mayoria del contenido educativo es en ingles. Mi hijo de 4 anos no entiende.", "ui spanish content english", False, "la interfaz esta en espanol pero la mayoria del contenido es en ingles"),
            (2, "Voz robotica", "La voz en espanol suena robotica y mal acentuada. Distrae mas que ensena.", "robotic spanish voice", False, "voz en espanol suena robotica"),
            (1, "Faltan actividades en espanol", "Muchas actividades simplemente no estan disponibles en espanol. Aparece un mensaje de 'proximamente'.", "many activities missing in spanish", False, "no estan disponibles en espanol"),
        ],
    ),
    # ---------- What to Expect / notifications_ads / US ----------
    dict(
        app="What to Expect", cat="pregnancy", country="us", lang="en", category_key="notifications_ads",
        variations=[
            (1, "Sponsored everywhere", "80% of articles are sponsored content from formula companies. Hard to find unbiased info.", "sponsored content overload", False, "80% of articles are sponsored content"),
            (2, "Ad clutter", "Every screen has 3 ads. I cant focus on the content for the ad noise.", "ad clutter", False, "every screen has 3 ads"),
            (2, "Push spam", "Multiple pushes per day. 'Did you know your baby is the size of an avocado?' Yes I know, you told me yesterday.", "redundant push notifications", False, "multiple pushes per day"),
        ],
    ),

    # ============ POSITIVE-SENTIMENT CLUSTERS (Competitor Strengths) ============

    # ---------- Lovevery / content_quality / US (POSITIVE) ----------
    dict(
        app="Lovevery", cat="competitor", country="us", lang="en", category_key="content_quality",
        sentiment="positive",
        variations=[
            (5, "Worth every penny", "The activities are genuinely research-backed and my daughter is actually engaged. You can tell real experts designed these.", "research-backed activities", False, "genuinely research-backed and my daughter is actually engaged"),
            (5, "Best parenting app", "Activities scale beautifully with developmental stage. I've tried 6 other apps and nothing comes close.", "stage-perfect progression", True, "nothing comes close"),
            (4, "Real depth", "Finally a parenting app that doesn't talk down to me. Real depth, real research, real progress with my son.", "real depth respects parents", False, "doesn't talk down to me"),
            (5, "Excellent content", "Every kit comes with content that explains the WHY behind each activity. That changes how I parent.", "explains the why", False, "explains the WHY behind each activity"),
            (5, "Pediatrician recommended", "Our pediatrician actually recommended this. The activities align with developmental milestones perfectly.", "pediatrician recommended", True, "pediatrician actually recommended this"),
        ],
    ),
    # ---------- Huckleberry / features_breadth / US (POSITIVE) ----------
    dict(
        app="Huckleberry", cat="tracker", country="us", lang="en", category_key="features_breadth",
        sentiment="positive",
        variations=[
            (5, "Sleep saver", "The SweetSpot predictions are uncanny. My baby actually sleeps now. Worth every penny of the premium subscription.", "sweetspot sleep predictions", True, "my baby actually sleeps now"),
            (5, "Multi-caregiver works", "Husband and I both log in real time and it just works. No conflicts, no sync issues. Finally.", "real-time multi-caregiver", False, "husband and I both log in real time and it just works"),
            (4, "Great feature depth", "Tracks everything I need plus things I didn't know I needed. Sleep coaching, growth, milestones, all in one.", "everything-in-one", False, "tracks everything I need plus things I didn't know I needed"),
            (5, "Pediatrician export", "The pediatrician export saved me at our 6-month visit. She loved seeing the data laid out professionally.", "pediatrician export feature", False, "the pediatrician export saved me"),
        ],
    ),
    # ---------- Khan Academy Kids / content_quality / US (POSITIVE) ----------
    dict(
        app="Khan Academy Kids", cat="early_education", country="us", lang="en", category_key="content_quality",
        sentiment="positive",
        variations=[
            (5, "Best free app", "Hard to believe this is free. Educational quality is genuinely better than the $15/month subscription apps we tried.", "free + high quality", True, "hard to believe this is free"),
            (5, "My toddler loves it", "My 3 year old asks for it by name. Content is engaging without being overstimulating like Cocomelon Play.", "engaging not overstimulating", False, "asks for it by name"),
            (4, "Real learning", "She actually learned letter sounds and counting from this app. Not just entertainment dressed up as education.", "real measurable learning", False, "actually learned letter sounds"),
            (5, "Trust the brand", "I trust Khan Academy more than any other kids app. No ads, no upsells, no shady data practices.", "trustworthy brand", False, "no ads no upsells no shady data practices"),
        ],
    ),
    # ---------- Bebbo / trust_credibility / BR (POSITIVE) ----------
    dict(
        app="Bebbo", cat="competitor", country="br", lang="pt", category_key="trust_credibility",
        sentiment="positive",
        variations=[
            (5, "UNICEF da confianca", "Saber que e da UNICEF muda tudo. Posso confiar nas informacoes. Outras apps inventam coisas, essa nao.", "unicef-backed credibility", True, "saber que e da UNICEF muda tudo"),
            (5, "Conteudo confiavel", "Finalmente uma app com informacao real, baseada em evidencias. Recomendo para todas as maes que conheco.", "evidence-based content", False, "informacao real baseada em evidencias"),
            (4, "Tudo gratis e bom", "Gratuita, sem propaganda, e com conteudo de qualidade da UNICEF. Como pode ser tao boa de graca?", "free no ads quality", False, "como pode ser tao boa de graca"),
            (5, "Pediatra recomendou", "Meu pediatra recomendou o Bebbo. Disse que e a unica app de crianca que confia.", "pediatrician recommended", False, "a unica app de crianca que confia"),
        ],
    ),
    # ---------- Pampers Rewards / customer_support / US (POSITIVE) ----------
    dict(
        app="Pampers Rewards", cat="brand_product", country="us", lang="en", category_key="customer_support",
        sentiment="positive",
        variations=[
            (5, "Real human responses", "Submitted a question about a missing reward and got a real human reply in 2 hours. Refunded the points within the same day.", "fast human reply", False, "got a real human reply in 2 hours"),
            (5, "They actually help", "Lost my receipts in a phone migration. Support manually credited the points after I sent photos. That's service.", "manual point credit", False, "manually credited the points after I sent photos"),
            (4, "Great customer service", "Honestly the best customer service of any rewards program I've used. Diaper companies should take notes.", "best in category", False, "best customer service of any rewards program"),
        ],
    ),
]


def build_rows():
    review_rows = []
    class_rows = []
    counter = 0
    for cluster in CLUSTERS:
        cluster_sentiment = cluster.get("sentiment")   # explicit sentiment for positive clusters
        for v_idx, (rating, title, body, sub_reason, churn, quote) in enumerate(cluster["variations"]):
            counter += 1
            # Disambiguate the review_id when a cluster has the same (app,country,category)
            # but a different sentiment direction.
            sent_tag = f":{cluster_sentiment}" if cluster_sentiment else ""
            review_id = f"demo:{cluster['app'].lower().replace(' ', '_')}:{cluster['country']}:{cluster['category_key']}{sent_tag}:{v_idx}"
            review_date = _date(days_ago=(counter * 2) % 85 + 1)  # spread across last ~85 days
            review_rows.append((
                review_id,
                "demo",                              # store
                cluster["app"],                       # app_name
                cluster["cat"],                       # app_category
                cluster["country"],                   # country
                cluster["lang"],                      # lang
                rating,
                title,
                body,
                "demo_seed_author",                  # author
                review_date,
                "demo",                              # app_version
            ))
            if cluster_sentiment:
                sentiment = cluster_sentiment
            elif rating >= 4:
                sentiment = "positive"
            elif rating == 3:
                sentiment = "mixed"
            else:
                sentiment = "negative"
            class_rows.append((
                review_id,
                cluster["category_key"],
                sub_reason,
                sentiment,
                churn,
                quote,
                0.92,                                # confidence
                MODEL_TAG,
            ))
    return review_rows, class_rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--purge", action="store_true", help="Delete all demo:* rows and exit")
    p.add_argument("--replace", action="store_true", help="Purge then re-insert")
    args = p.parse_args()

    con = connect()

    if args.purge or args.replace:
        purged_class = con.execute("DELETE FROM classifications WHERE review_id LIKE 'demo:%'").fetchall()
        purged_rev = con.execute("DELETE FROM reviews WHERE review_id LIKE 'demo:%'").fetchall()
        log.info("Purged demo rows.")
        if args.purge and not args.replace:
            con.close()
            return

    review_rows, class_rows = build_rows()
    con.executemany(
        """
        INSERT OR REPLACE INTO reviews
            (review_id, store, app_name, app_category, country, lang,
             rating, title, body, author, review_date, app_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        review_rows,
    )
    con.executemany(
        """
        INSERT OR REPLACE INTO classifications
            (review_id, category_key, sub_reason, sentiment, is_churn_signal,
             verbatim_quote, confidence, model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        class_rows,
    )
    log.info("Inserted %d demo reviews + %d demo classifications.", len(review_rows), len(class_rows))
    log.info("Apps: %s", sorted({r[2] for r in review_rows}))
    log.info("Markets: %s", sorted({r[4] for r in review_rows}))
    log.info("Categories: %s", sorted({c[1] for c in class_rows}))
    log.info("\nTo remove later: python -m scripts.seed_demo_data --purge")
    con.close()


if __name__ == "__main__":
    main()
