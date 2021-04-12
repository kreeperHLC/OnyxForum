# -*- coding: utf-8 -*-
import os

from pluggy import HookimplMarker
import discord
import traceback

from flaskbb.utils.helpers import render_template
from flask import current_app, url_for

from .views import hub
from .permissions import can_access_hub

__version__ = "1.0.0"
SETTINGS = None


hookimpl = HookimplMarker("flaskbb")


@hookimpl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")


@hookimpl
def flaskbb_load_translations():
    return os.path.join(os.path.dirname(__file__), "translations")


@hookimpl
def flaskbb_load_blueprints(app):
    app.register_blueprint(
        hub, url_prefix=app.config.get("PLUGIN_HUB_URL_PREFIX", "/hub")
    )


@hookimpl
def flaskbb_tpl_navigation_before():
    return render_template("hub/navigation_snippet.html")


@hookimpl
def flaskbb_jinja_directives(app):
    app.jinja_env.filters["can_access_hub"] = can_access_hub

@hookimpl
def flaskbb_event_topic_save_after(topic, is_new):
    if "SENAT_FORUM_ID" not in current_app.config or "SENAT_JOURNAL_WEBHOOK" not in current_app.config:
        print("SENAT_JOURNAL isn't configured")
        return

    if not is_new:
        return

    if topic.forum_id == current_app.config["SENAT_FORUM_ID"]:
        try:
            webhook = discord.Webhook.from_url(current_app.config["SENAT_JOURNAL_WEBHOOK"], adapter=discord.RequestsWebhookAdapter())

            desc = topic.first_post.content
            desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc

            url = url_for("forum.view_topic", topic_id=topic.id, slug=topic.slug, _external=True)
            embed = discord.Embed(title=topic.title, description=desc, url=url)
            embed.add_field(name="Author:", value=topic.user.display_name)

            webhook.send(embed=embed)
        except Exception:
            print(traceback.format_exc())
